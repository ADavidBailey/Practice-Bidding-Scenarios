#!/usr/bin/env python3
"""play_promote.py — PROMOTE consumer for the play-[PLAY] automation machine.

Reads the GATE's verdict (Trainer's verify_play_coaching.py, captured to
coaching-curated/.work/<scn>-play-verdict.json) and reconciles
coaching-curated/<scn>.pbn to it, BIAS-TO-DROP:

  KEEP       -> keep the [PLAY]; if recommended_accept is non-empty, ensure an
                [ACCEPT \\Xr ...] line sits between the PRESENT prose and [WHY]
                (so the quiz never dings a double-dummy-correct play).
  DROP       -> strip the whole [PLAY..WHY] decision (board degrades to tips-only;
                it still plays manually).
  QUARANTINE -> strip it too (nothing wrong ships) AND log to
                .work/<scn>-quarantine.log for the downstream Report/Issue human.

A decision in the .pbn with NO matching verdict is DROPPED (fail-safe: an
un-screened decision never promotes). After reconciling, run promote.py to push
the gated curated file to served coaching/.

Stateless / idempotent: re-deriving the verdict and re-running reproduces the
same reconciled file. Cold-resumable — matches the gate's design.

Usage:
  python3 -P py/play_promote.py <scenario>            # dry run: show actions
  python3 -P py/play_promote.py <scenario> --apply    # rewrite coaching-curated/<scn>.pbn
"""
import sys, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUR = os.path.join(ROOT, "coaching-curated")
WORK = os.path.join(CUR, ".work")
GLYPH = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}


def _decisions(block):
    """Yield (match_start, match_end, trick, seat, suit, rank, body) for each
    [PLAY] decision inside a board's coaching block. A decision runs from its
    [PLAY ...] header to the next [PLAY or the closing brace."""
    for m in re.finditer(
            r'\[PLAY\s+(\d+)\s+([NSEW])\s+\\([SHDC])([AKQJT2-9])\](.*?)'
            r'(?=\n\[PLAY\s|\n?\}|\Z)', block, flags=re.S):
        yield m.start(), m.end(), m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)


def _accept_line(cards):
    return "[ACCEPT " + " ".join(f"\\{c[0]}{c[1:]}" for c in cards) + "]"


def reconcile(scn, apply):
    vp = os.path.join(WORK, f"{scn}-play-verdict.json")
    if not os.path.exists(vp):
        sys.exit(f"no verdict file {vp} — capture the gate's --json there first")
    verdicts = json.load(open(vp))
    # key by (board, trick, seat, card) so multiple decisions per board resolve
    vmap = {(str(v['board']), int(v['trick']), v['seat'], v['card'].upper()): v
            for v in verdicts}
    path = os.path.join(CUR, f"{scn}.pbn")
    text = open(path, encoding='utf-8', errors='replace').read()
    chunks = re.split(r'(?=\[Board ")', text)
    counts = {'KEEP': 0, 'DROP': 0, 'QUARANTINE': 0, 'UNMATCHED-DROP': 0, 'accept-added': 0}
    quarantined = []
    out = []
    for ch in chunks:
        bm = re.search(r'\[Board "([^"]+)"\]', ch)
        if not bm:
            out.append(ch); continue
        board = bm.group(1)
        # the COACHING block is the one holding the [ROLE]/[STAGE] tips (not the
        # preceding {Shape}/{HCP}/{Curate} blocks). Its prose carries no braces,
        # so it runs from '{[ROLE' to the next '}'.
        cm = re.search(r'\{\[ROLE', ch)
        if not cm:
            out.append(ch); continue
        bs = cm.start(); be = ch.find('}', bs)
        if be < 0 or '[PLAY' not in ch[bs:be]:
            out.append(ch); continue
        block = ch[bs:be]
        # process decisions right-to-left so edits don't shift earlier offsets
        edits = []
        for s, e, trick, seat, suit, rank, body in _decisions(block):
            card = f"{suit}{rank}"
            v = vmap.get((board, int(trick), seat, card))
            status = v['status'] if v else 'UNMATCHED-DROP'
            if status == 'KEEP':
                counts['KEEP'] += 1
                acc = v.get('recommended_accept') or []
                if acc and '[ACCEPT' not in body:
                    wm = re.search(r'\n\[WHY\]', body)
                    if wm:
                        newbody = body[:wm.start()] + "\n" + _accept_line(acc) + body[wm.start():]
                        edits.append((s, e, block[s:e].replace(body, newbody)))
                        counts['accept-added'] += 1
            else:  # DROP / QUARANTINE / UNMATCHED-DROP -> strip the decision
                counts[status if status in counts else 'DROP'] += 1
                if status == 'QUARANTINE':
                    quarantined.append({'board': board, 'trick': int(trick), 'seat': seat,
                                        'card': card, 'reason': (v or {}).get('reason', '')})
                # remove decision + the blank line(s) that precede it
                cut = s
                while cut > 0 and block[cut-1] == '\n':
                    cut -= 1
                edits.append((cut, e, ''))
        for s, e, repl in sorted(edits, key=lambda x: -x[0]):
            block = block[:s] + repl + block[e:]
        out.append(ch[:bs] + block + ch[be:])
    summary = (f"{scn}: KEEP={counts['KEEP']} DROP={counts['DROP']} "
               f"QUARANTINE={counts['QUARANTINE']} unmatched-drop={counts['UNMATCHED-DROP']} "
               f"| [ACCEPT] added={counts['accept-added']}")
    if apply:
        open(path, 'w').write("".join(out))
        if quarantined:
            with open(os.path.join(WORK, f"{scn}-quarantine.log"), 'w') as f:
                for q in quarantined:
                    f.write(json.dumps(q) + "\n")
        print("APPLIED  " + summary)
        print(f"  reconciled {path}; next: python3 -P py/promote.py {scn}")
    else:
        print("DRY RUN  " + summary + "  (use --apply to write)")
    return counts


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if x != "--apply"]
    if not a:
        sys.exit(__doc__)
    reconcile(a[0], "--apply" in sys.argv)
