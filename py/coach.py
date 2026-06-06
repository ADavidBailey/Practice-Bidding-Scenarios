#!/usr/bin/env python3
"""coach.py — mechanics of coaching generation (see coaching-curated/GENERATOR.md).

Two steps bracket the Claude-subagent prose generation:

  python3 py/coach.py packets <scenario> [query...] [-n N]
      Select curated boards from bba-curated/<scenario>.pbn (default
      "bidding=textbook,judgment diff<=3", N=30), write the selected input
      PBN and per-chunk packet JSON into coaching-curated/.work/ for the
      subagents to coach.

  python3 py/coach.py splice <scenario>
      Splice the subagents' {board,coaching} JSON (coaching-curated/.work/
      <scenario>-coach*.json) into the selected input and write
      coaching-curated/<scenario>.pbn. Validates pronoun tokens and that no
      [BID Pass] slipped in.

The prose itself is written by Claude subagents following GENERATOR.md;
this script only does the deterministic selection and splice.
"""
import sys, os, re, json, glob
sys.path.append(os.path.dirname(__file__))
from curate import split_boards, tag, hands, deal_hash

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUR = os.path.join(ROOT, "bba-curated")
OUT = os.path.join(ROOT, "coaching-curated")
WORK = os.path.join(OUT, ".work")
HCP = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
LHO = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}


def _curate_block(ch):
    m = re.search(r'\{Curate\n(.*?)\n\}', ch, flags=re.S)
    d = {}
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                d[k.strip()] = v.strip()
    return d


def _match(blk, term):
    m = re.match(r'([\w-]+)\s*(<=|>=|=)\s*(.+)', term)
    key, op, val = m.group(1), m.group(2), m.group(3).strip()
    if key == 'diff':
        d = blk.get('difficulty')
        if d is None:
            return False
        d, v = int(d), int(val)
        return d <= v if op == '<=' else d >= v if op == '>=' else d == v
    content = blk.get(key)
    if content is None:
        return False
    words = content.split()
    return any(v.strip() in words for v in val.split(','))


def packets(scn, terms, n):
    src = os.path.join(CUR, f"{scn}.pbn")
    chunks = split_boards(src)
    sel = [ch for ch in chunks if all(_match(_curate_block(ch), t) for t in terms)][:n]
    os.makedirs(WORK, exist_ok=True)
    # selected input PBN, Curate blocks stripped (the generator doesn't need them)
    inp = "".join(re.sub(r'\{Curate\n.*?\n\}\n', '', ch, flags=re.S) for ch in sel)
    open(os.path.join(WORK, f"{scn}-input.pbn"), "w").write(inp)
    # packets (split into chunks of 15 for parallel subagents)
    pkts = []
    for ch in sel:
        blk = _curate_block(ch)
        deal = tag(ch, 'Deal'); h = hands(deal)
        m = re.search(r'\[Auction "(\w)"\]\s*\n((?:[^\[{][^\n]*\n?)*)', ch)
        dec = tag(ch, 'Declarer')
        pkts.append({
            "board": tag(ch, 'Board'), "dealer": tag(ch, 'Dealer'),
            "vul": tag(ch, 'Vulnerable'),
            "hands": {s: " ".join(f"{su}:{''.join(h[s][i]) or '-'}"
                                  for i, su in enumerate("SHDC")) for s in "NESW"},
            "hcp": {s: sum(HCP.get(c, 0) for su in h[s] for c in su) for s in "NESW"},
            "auction": " ".join(m.group(2).split()) if m else None,
            "contract": tag(ch, 'Contract'), "declarer": dec,
            "opening_leader": LHO.get(dec) if dec in LHO else None,
            "bidding_tier": blk.get('bidding', '').split()[0] if blk.get('bidding') else '?',
            "also_ok": blk.get('also-ok', ''),
            "note": blk.get('bidding-note', ''),
        })
    size = (len(pkts) + 1) // 2 or 1
    for i in range(0, len(pkts), size):
        k = i // size + 1
        json.dump(pkts[i:i+size], open(os.path.join(WORK, f"{scn}-pkt{k}.json"), "w"), indent=0)
    print(f"{scn}: selected {len(sel)} boards -> {WORK}/{scn}-input.pbn")
    print(f"  packets: {(len(pkts)+size-1)//size} files ({size}/file)")
    print(f"  next: a subagent per packet writes {scn}-coach<k>.json per GENERATOR.md")


def splice(scn):
    coach = {}
    for f in sorted(glob.glob(os.path.join(WORK, f"{scn}-coach*.json"))):
        for o in json.load(open(f)):
            coach[str(o['board'])] = o['coaching'].strip()
    if not coach:
        sys.exit(f"no {scn}-coach*.json in {WORK} — run the subagents first")
    out = []
    for ch in split_boards(os.path.join(WORK, f"{scn}-input.pbn")):
        b = tag(ch, 'Board'); body = coach.get(str(b))
        if body:
            m = re.search(r'(\[Auction "[^"]*"\]\n(?:[^\[{][^\n]*\n)*)', ch)
            if m:
                ch = ch[:m.end()] + "{" + body + "}\n" + ch[m.end():]
        out.append(ch)
    txt = "".join(out)
    # validation
    bidpass = txt.count('[BID Pass]')
    recites = len(re.findall(r'\\[SHDC]\s?[AKQJT2-9]{2,}', txt))
    open(os.path.join(OUT, f"{scn}.pbn"), "w").write(txt)
    coached = sum(1 for ch in split_boards(os.path.join(OUT, f"{scn}.pbn"))
                  if re.search(r'\[Auction[^\]]*\]\n(?:[^\[{][^\n]*\n)*\{', ch))
    print(f"{scn}: wrote {OUT}/{scn}.pbn — {coached} coached boards, "
          f"{txt.count('[BID')} [BID anchors")
    if bidpass:
        print(f"  WARNING: {bidpass} [BID Pass] anchors (should be 0)")
    if recites:
        print(f"  WARNING: {recites} possible card recitations (should be 0)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("packets", "splice"):
        sys.exit(__doc__)
    cmd, scn = a[0], a[1]
    if cmd == "splice":
        splice(scn)
    else:
        rest = a[2:]
        n = 30
        if "-n" in rest:
            i = rest.index("-n"); n = int(rest[i+1]); del rest[i:i+2]
        terms = rest or ["bidding=textbook,judgment", "diff<=3"]
        packets(scn, terms, n)
