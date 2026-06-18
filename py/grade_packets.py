#!/usr/bin/env python3
"""grade_packets.py — Layer B (Claude grading) input/assembly helper for
BIDDING scenarios. Bridges curate.py (Layer A features) and annotate.py.

emit <scn> [--all] [--chunk N]
    Build per-board grading inputs from bba/<scn>.pbn + the Layer A features
    in bba-curated/.progress/<scn>-pool.jsonl. By default only the
    intended-auction subset (in_bba_filtered) is emitted (bidding lessons only
    need the boards where BBA actually bid the convention); --all emits the
    whole pool. Writes coaching-curated/.work/<scn>-grade-in-<i>.json chunks,
    each a list of {board, deal_hash, dealer, vul, deal, auction, contract,
    result, score, hcp, flags, dd_class, in_bba_filtered, matched_intended_auction}.

assemble <scn>
    Merge the subagents' coaching-curated/.work/<scn>-grade-out-*.json verdict
    files into bba-curated/<scn>-graded.json (shape {scenario, graded,
    aggregates, verdicts}). Then run: python3 -P py/annotate.py <scn>.
"""
import sys, os, re, json, glob, collections
sys.path.append(os.path.dirname(__file__))
from curate import split_boards, tag, deal_hash

WORK = "coaching-curated/.work"


def _auction_text(chunk):
    m = re.search(r'\[Auction\s+"[^"]*"\]', chunk)
    if not m:
        return ""
    tail = chunk[m.end():]
    end = tail.find('{')
    if end == -1:
        end = len(tail)
    return tail[:end].strip()


def _filtered_hashes(scn):
    hs = set()
    p = f"bba-filtered/{scn}.pbn"
    if os.path.exists(p):
        for ch in split_boards(p):
            d = tag(ch, 'Deal')
            if d:
                hs.add(deal_hash(d))
    return hs


def emit(scn, all_boards=False, chunk=40):
    feats = {}
    jl = f"bba-curated/.progress/{scn}-pool.jsonl"
    for line in open(jl):
        r = json.loads(line)
        feats[r['board']] = r
    filtered = _filtered_hashes(scn)
    rows = []
    for ch in split_boards(f"bba/{scn}.pbn"):
        bd = tag(ch, 'Board'); d = tag(ch, 'Deal')
        if not d:
            continue
        h = deal_hash(d)
        in_filt = h in filtered
        if not all_boards and not in_filt:
            continue
        f = feats.get(bd, {})
        rows.append({
            "board": bd, "deal_hash": h,
            "dealer": tag(ch, 'Dealer'), "vul": tag(ch, 'Vulnerable'),
            "deal": d, "auction": _auction_text(ch),
            "contract": tag(ch, 'Contract'), "result": tag(ch, 'Result'),
            "score": tag(ch, 'Score'),
            "hcp": f.get('hcp'), "flags": f.get('flags', []),
            "dd_class": f.get('dd_class'),
            "in_bba_filtered": in_filt,
            "matched_intended_auction": f.get('matched_intended_auction'),
        })
    os.makedirs(WORK, exist_ok=True)
    for old in glob.glob(f"{WORK}/{scn}-grade-in-*.json"):
        os.remove(old)
    n = 0
    for i in range(0, len(rows), chunk):
        with open(f"{WORK}/{scn}-grade-in-{n}.json", "w") as fh:
            json.dump(rows[i:i+chunk], fh, indent=1)
        n += 1
    print(f"{scn}: emitted {len(rows)} boards "
          f"({'full pool' if all_boards else 'intended-auction subset'}) "
          f"-> {n} chunk(s) in {WORK}/{scn}-grade-in-*.json")


def assemble(scn):
    verdicts = []
    seen = set()
    for p in sorted(glob.glob(f"{WORK}/{scn}-grade-out-*.json")):
        for v in json.load(open(p)):
            h = v.get('deal_hash')
            if h in seen:
                continue
            seen.add(h)
            verdicts.append(v)
    agg = collections.Counter(v['bidding']['tier'] for v in verdicts)
    out = {"scenario": scn, "graded": len(verdicts),
           "aggregates": {"bidding_tiers": dict(agg)},
           "verdicts": verdicts}
    path = f"bba-curated/{scn}-graded.json"
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"{scn}: assembled {len(verdicts)} verdicts -> {path}")
    print(f"  bidding tiers: {dict(agg)}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    scn = sys.argv[2]
    if cmd == "emit":
        emit(scn, all_boards="--all" in sys.argv,
             chunk=int(next((a.split("=")[-1] for a in sys.argv if a.startswith("--chunk")), 40)))
    elif cmd == "assemble":
        assemble(scn)
