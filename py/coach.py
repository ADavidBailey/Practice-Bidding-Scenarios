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
from curate import split_boards, tag, hands, deal_hash, opening_lead_vs_nt, SUITS
from suit_tricks import trick_map

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
    validate(scn)  # structure gate: flags N/S calls missing a [BID] anchor


def _norm_call(s):
    s = s.strip().upper()
    return s + "T" if re.fullmatch(r"\d+N", s) else s


LHO = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}


def play_packets(scn, theme, n):
    """Select curated boards graded declarer textbook/standard for THEME and
    build play-coaching packets (deal + contract + declarer + leader + note)."""
    src = os.path.join(CUR, f"{scn}.pbn")
    graded = {v['deal_hash']: v for v in
              json.load(open(os.path.join(CUR, f"{scn}-graded.json")))['verdicts']}
    pkts = []
    for ch in split_boards(src):
        d = tag(ch, 'Deal'); v = graded.get(deal_hash(d)) if d else None
        if not v:
            continue
        decl = v.get('declarer', {})  # declarer-play GRADING (tier/themes/note)
        tier = decl.get('tier'); themes = decl.get('themes', []); note = decl.get('note', '')
        if tier not in ('textbook', 'standard') or theme not in themes:
            continue
        h = hands(d); declarer = tag(ch, 'Declarer')  # the declaring SEAT
        # VERIFIED trick facts (exact double-dummy, known cards) so the
        # subagent narrates numbers instead of counting them itself. 'top' =
        # immediate cash-out winners NS hold in the suit; 'establishable' =
        # tricks after forcing out opponents' higher honours; 'development_suit'
        # = the suit that yields the most NEW tricks (the ninth-trick source).
        tmap = trick_map(h)
        leadseat = LHO.get(declarer)
        ol = opening_lead_vs_nt(h[leadseat])           # computed standard NT lead
        lead = f"\\{SUITS[ol[0]]}{ol[1]}" if ol else None
        pkts.append({
            "board": tag(ch, 'Board'), "contract": tag(ch, 'Contract'),
            "declarer": declarer, "leader": leadseat,
            "dealer": tag(ch, 'Dealer'), "vul": tag(ch, 'Vulnerable'),
            "theme": theme, "note": note,
            "opening_lead": lead,   # AUTHORITATIVE — use this card verbatim
            "hands": {s: " ".join(f"{su}:{''.join(h[s][i]) or '-'}"
                                  for i, su in enumerate("SHDC")) for s in "NESW"},
            "trick_map": tmap,
        })
        if len(pkts) >= n:
            break
    os.makedirs(WORK, exist_ok=True)
    size = (len(pkts) + 1) // 2 or 1
    for i in range(0, len(pkts), size):
        json.dump(pkts[i:i+size], open(os.path.join(WORK, f"{scn}-play-pkt{i//size+1}.json"), "w"), indent=0)
    json.dump([p['board'] for p in pkts],
              open(os.path.join(WORK, f"{scn}-play-boards.json"), "w"))
    print(f"{scn}: {len(pkts)} '{theme}' boards -> {(len(pkts)+size-1)//size} play packets")
    print(f"  next: a subagent per packet writes tips per GENERATOR-PLAY.md -> {scn}-play-coach<k>.json")


def play_splice(scn):
    """Splice [ROLE]/[STAGE] play tips after each selected board's auction."""
    tips = {}
    for f in sorted(glob.glob(os.path.join(WORK, f"{scn}-play-coach*.json"))):
        for o in json.load(open(f)):
            tips[str(o['board'])] = o['coaching'].strip()
    if not tips:
        sys.exit(f"no {scn}-play-coach*.json in {WORK}")
    boards = set(json.load(open(os.path.join(WORK, f"{scn}-play-boards.json"))))
    out = []
    for ch in split_boards(os.path.join(CUR, f"{scn}.pbn")):
        b = tag(ch, 'Board')
        if str(b) in boards and str(b) in tips:
            m = re.search(r'(\[Auction "[^"]*"\]\n(?:[^\[{][^\n]*\n)*)', ch)
            if m:
                ch = ch[:m.end()] + "{" + tips[str(b)] + "}\n" + ch[m.end():]
        out.append(ch)
    txt = "".join(out)
    open(os.path.join(OUT, f"{scn}.pbn"), "w").write(txt)
    # validation: pre-lead card present + no space; matches the computed lead
    coached = [b for b in boards if b in tips]
    nolead = [b for b in coached if not re.search(r'\[ROLE leader\]\[STAGE pre-lead\]\s*Lead the \\[SHDC][AKQJT2-9]', tips[b])]
    spacelead = [b for b in coached if re.search(r'Lead the \\[SHDC]\s+[AKQJT2-9]', tips[b])]
    # cross-check the spliced lead card against the standard NT lead from the
    # leader's hand (the card is auto-played, so it must be the right one).
    wronglead = []
    deals = {tag(ch, 'Board'): tag(ch, 'Deal') for ch in split_boards(os.path.join(CUR, f"{scn}.pbn"))}
    for b in coached:
        d = deals.get(b)
        if not d:
            continue
        m = re.search(r'Lead the (\\[SHDC][AKQJT2-9])', tips[b])
        h = hands(d); decl = None
        dm = re.search(r'\[Declarer "(\w)"\]', "")  # declarer seat unused; recompute leader
        # leader = LHO of declarer; declarer seat from PBN
        for ch in split_boards(os.path.join(CUR, f"{scn}.pbn")):
            if tag(ch, 'Board') == b:
                decl = tag(ch, 'Declarer'); break
        if not (m and decl):
            continue
        ol = opening_lead_vs_nt(h[LHO.get(decl)])
        want = f"\\{SUITS[ol[0]]}{ol[1]}" if ol else None
        if want and m.group(1) != want:
            wronglead.append(f"{b}:{m.group(1)}!={want}")
    print(f"{scn}: spliced play tips into {len(coached)} boards -> {OUT}/{scn}.pbn")
    if nolead:
        print(f"  WARNING: {len(nolead)} boards missing a load-bearing 'Lead the \\Xr' pre-lead: {sorted(nolead)}")
    if spacelead:
        print(f"  WARNING: space before lead rank (breaks auto-lead): {sorted(spacelead)}")
    if wronglead:
        print(f"  WARNING: pre-lead card != standard lead: {sorted(wronglead)}")


def validate(scn):
    """Check coaching-curated/<scn>.pbn structure: every non-pass call has
    exactly one anchored [BID] chunk, intro carries no [BID], [ACCEPT] sits
    only on a non-pass [BID] chunk, and no [BID] fails to anchor. Reports
    per-board issues; returns the count."""
    path = os.path.join(OUT, f"{scn}.pbn")
    SEATS = ['N', 'E', 'S', 'W']
    CALL_RE = re.compile(r'(?i)^(pass|x|xx|ap|\d[cdhsn]t?)$')
    issues = 0
    for ch in split_boards(path):
        b = tag(ch, 'Board')
        m = re.search(r'\[Auction "(\w)"\]\s*\n((?:[^\[{][^\n]*\n?)*)', ch)
        dealer = m.group(1) if m else 'N'
        # keep only real calls (drop alert refs like =1=, !, etc.)
        raw = [t for t in (m.group(2).split() if m else []) if CALL_RE.match(t)]
        di = SEATS.index(dealer)
        # coached side = N/S; collect their non-pass calls in order
        coached = [_norm_call(c) for j, c in enumerate(raw)
                   if SEATS[(di + j) % 4] in ('N', 'S') and _norm_call(c) != 'PASS']
        a = ch.find('[Auction'); i = ch.find('{', a)
        if i < 0:
            print(f"  {scn} b{b}: no coaching block"); issues += 1; continue
        body = ch[i:ch.find('}', i)]
        bids = re.findall(r'\[BID\s+([^\]]+)\]', body)
        nbids = [_norm_call(x) for x in bids]
        probs = []
        # Every coached-side (N/S) non-pass call must have a [BID] anchor (so
        # rotation can quiz it and [ACCEPT] can attach). Extra [BID]s on
        # opponents' calls are allowed (context narration, never quizzed).
        import collections as _c
        missing = _c.Counter(coached) - _c.Counter(nbids)
        if missing:
            probs.append(f"N/S calls with no [BID]: {sorted(missing.elements())}")
        # Only [show NS] is allowed (it introduces the post-auction reflection).
        # Any other [show X] inside a [BID] chunk makes the trainer DEFER that
        # prose to post-auction, where it renders in the wrong person.
        bad_show = [m.group(1) for m in re.finditer(r'\[show\s+([^\]]+)\]', body)
                    if m.group(1).strip() != 'NS']
        if bad_show:
            probs.append(f"mid-auction [show {bad_show}] — defers/scrambles prose (only [show NS] allowed)")
        # [ACCEPT] must follow a [BID <non-pass>] and not be on a Pass/opening-only
        for am in re.finditer(r'\[ACCEPT\s+([^\]]+)\]', body):
            pre = body[:am.start()]
            host = re.findall(r'\[BID\s+([^\]]+)\]', pre)
            if not host:
                probs.append(f"[ACCEPT {am.group(1)}] not inside any [BID] chunk")
        if probs:
            issues += 1
            print(f"  {scn} b{b}: " + "; ".join(probs))
    print(f"{scn}: {issues} board(s) with structure issues")
    return issues


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("packets", "splice", "validate", "play-packets", "play-splice"):
        sys.exit(__doc__)
    if a[0] == "validate":
        for scn in a[1:]:
            validate(scn)
        sys.exit(0)
    if a[0] == "play-splice":
        play_splice(a[1])
        sys.exit(0)
    if a[0] == "play-packets":
        rest = a[2:]; n = 30
        if "-n" in rest:
            i = rest.index("-n"); n = int(rest[i+1]); del rest[i:i+2]
        theme = rest[0] if rest else "hold-up"
        play_packets(a[1], theme, n)
        sys.exit(0)
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
