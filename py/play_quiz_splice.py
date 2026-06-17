#!/usr/bin/env python3
r"""play_quiz_splice.py — AUTHOR-side splice for the [PLAY] play-quiz layer.

The 4-stage [ROLE]/[STAGE] tips are already in coaching-curated/<scn>.pbn. This
tool ADDS the interactive [PLAY]/[ACCEPT]/[WHY] decisions on top of them, from a
structured author file so subagents never hand-edit PBN braces (the one step the
machine left free-hand). It is the AUTHOR-side counterpart of play_promote.py
(the PROMOTE side) and reuses its exact coaching-block geometry.

Author file (one per scenario), written by the fan-out subagents:
  coaching-curated/.work/<scn>-play-quiz.json
  [ {"board":"44","trick":6,"seat":"S","card":"HQ",
     "present":"...PRESENT prose (withhold the answer)...",
     "why":"...WHY prose (may state the conclusion)...",
     "accept":["H3"]}        # optional co-correct cards
  ]
card / accept entries are suit-letter form ("HQ","H3") — the verdict schema.

Splice geometry (identical to play_promote): the coaching block runs from
'{[ROLE' to the next '}' (its prose carries no braces). The post-play tip's
prose abuts that '}'; we insert each decision as

    \n\n[PLAY t SEAT \Xr]\n<present>\n([ACCEPT \Xr ...]\n)?[WHY]\n<why>

so the LAST decision's <why> abuts the '}', matching the proven Finesse_Simple
format. Decisions stack in trick order.

IDEMPOTENT: any existing [PLAY..] decisions in a board's block are stripped
first, then the author file is re-applied — re-running reproduces the file
byte-for-byte. Boards with no entry in the author file are left untouched.

Usage:
  python3 -P py/play_quiz_splice.py <scn>            # dry run: show actions
  python3 -P py/play_quiz_splice.py <scn> --apply    # rewrite coaching-curated/<scn>.pbn
  python3 -P py/play_quiz_splice.py <scn> --extract   # dump existing [PLAY] -> author json
"""
import sys, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUR = os.path.join(ROOT, "coaching-curated")
WORK = os.path.join(CUR, ".work")
CARD_RE = re.compile(r'^[SHDC][AKQJT2-9]$')


def _coaching_span(ch):
    """(bs, be) of the {[ROLE...]} coaching block in a board chunk, or None.
    bs = '{' of '{[ROLE'; be = the matching '}' (prose carries no braces)."""
    cm = re.search(r'\{\[ROLE', ch)
    if not cm:
        return None
    be = ch.find('}', cm.start())
    return (cm.start(), be) if be >= 0 else None


def _strip_plays(block):
    """Return the block with any [PLAY..] decisions removed, trailing prose
    rstripped so it abuts the closing '}' again (the no-PLAY form)."""
    i = block.find('[PLAY')
    if i < 0:
        return block
    return block[:i].rstrip()


def _play_text(entry):
    t, seat, card = entry["trick"], entry["seat"], entry["card"]
    present = entry["present"].strip()
    why = entry["why"].strip()
    accept = entry.get("accept") or []
    acc = ("[ACCEPT " + " ".join(f"\\{c[0]}{c[1:]}" for c in accept) + "]\n") if accept else ""
    return f"\n\n[PLAY {t} {seat} \\{card[0]}{card[1:]}]\n{present}\n{acc}[WHY]\n{why}"


def _validate(entries, scn):
    errs = []
    cand_path = os.path.join(WORK, f"{scn}-play-candidates.json")
    cand = set()
    if os.path.exists(cand_path):
        cand = {(str(c["board"]), int(c["trick"]), c["seat"], c["card"].upper())
                for c in json.load(open(cand_path))}
    for e in entries:
        for k in ("board", "trick", "seat", "card", "present", "why"):
            if k not in e:
                errs.append(f"b{e.get('board','?')}: missing field '{k}'");
        if "card" in e and not CARD_RE.match(str(e["card"]).upper()):
            errs.append(f"b{e.get('board')}: bad card {e['card']!r}")
        for a in e.get("accept") or []:
            if not CARD_RE.match(str(a).upper()):
                errs.append(f"b{e.get('board')}: bad accept card {a!r}")
        key = (str(e.get("board")), int(e.get("trick", -1)), e.get("seat"),
               str(e.get("card", "")).upper())
        if cand and key not in cand:
            errs.append(f"b{e.get('board')}: {key[1:]} NOT a dd_line candidate "
                        f"(authoring off-screen decision — review)")
    return errs


def splice(scn, apply):
    qp = os.path.join(WORK, f"{scn}-play-quiz.json")
    if not os.path.exists(qp):
        sys.exit(f"no author file {qp}")
    entries = json.load(open(qp))
    errs = _validate(entries, scn)
    by_board = {}
    for e in entries:
        by_board.setdefault(str(e["board"]), []).append(e)
    for v in by_board.values():
        v.sort(key=lambda e: int(e["trick"]))
    path = os.path.join(CUR, f"{scn}.pbn")
    text = open(path, encoding="utf-8", errors="replace").read()
    chunks = re.split(r'(?=\[Board ")', text)
    out, touched, skipped = [], [], []
    for ch in chunks:
        bm = re.search(r'\[Board "([^"]+)"\]', ch)
        if not bm or bm.group(1) not in by_board:
            out.append(ch); continue
        board = bm.group(1)
        span = _coaching_span(ch)
        if not span:
            skipped.append(f"{board} (no {{[ROLE]}} block)"); out.append(ch); continue
        bs, be = span
        block = _strip_plays(ch[bs:be])
        block += "".join(_play_text(e) for e in by_board[board])
        out.append(ch[:bs] + block + ch[be:])
        touched.append(f"{board}:" + ",".join(f"t{e['trick']}\\{e['card']}" for e in by_board[board]))
    summary = (f"{scn}: {len(entries)} decision(s) on {len(by_board)} board(s) "
               f"-> spliced {len(touched)}")
    if errs:
        print("VALIDATION:")
        for e in errs:
            print(f"  !! {e}")
    print(f"  boards: {', '.join(touched) or '(none)'}")
    if skipped:
        print(f"  SKIPPED: {', '.join(skipped)}")
    if apply:
        if errs and any("missing field" in e or "bad card" in e for e in errs):
            sys.exit("refusing to apply: structural validation errors above")
        open(path, "w").write("".join(out))
        print(f"APPLIED -> {path}")
        print(f"  next: gate (verify_play_coaching.py {scn} --write-verdicts) "
              f"then py/play_promote.py {scn} --apply")
    else:
        print("DRY RUN (use --apply to write)")
    return touched


def extract(scn):
    """Dump a coached file's existing [PLAY] decisions back to the author json
    (for round-trip tests / re-deriving the quiz layer from a coached file)."""
    path = os.path.join(CUR, f"{scn}.pbn")
    text = open(path, encoding="utf-8", errors="replace").read()
    rows = []
    for ch in re.split(r'(?=\[Board ")', text):
        bm = re.search(r'\[Board "([^"]+)"\]', ch)
        span = _coaching_span(ch)
        if not (bm and span):
            continue
        block = ch[span[0]:span[1]]
        for m in re.finditer(
                r'\[PLAY\s+(\d+)\s+([NSEW])\s+\\([SHDC])([AKQJT2-9])\](.*?)'
                r'(?=\n\[PLAY\s|\n?\}|\Z)', block, flags=re.S):
            trick, seat, suit, rank, body = m.groups()
            acc = re.search(r'\[ACCEPT\s+([^\]]+)\]', body)
            accept = [a.replace("\\", "") for a in acc.group(1).split()] if acc else []
            present = body.split("[ACCEPT")[0].split("[WHY]")[0].strip()
            why = body.split("[WHY]", 1)[1].strip() if "[WHY]" in body else ""
            row = {"board": bm.group(1), "trick": int(trick), "seat": seat,
                   "card": f"{suit}{rank}", "present": present, "why": why}
            if accept:
                row["accept"] = accept
            rows.append(row)
    os.makedirs(WORK, exist_ok=True)
    out = os.path.join(WORK, f"{scn}-play-quiz.json")
    json.dump(rows, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"{scn}: extracted {len(rows)} [PLAY] decision(s) -> {out}")


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("-")]
    if not a:
        sys.exit(__doc__)
    if "--extract" in sys.argv:
        extract(a[0])
    else:
        splice(a[0], "--apply" in sys.argv)
