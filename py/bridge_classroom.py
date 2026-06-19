#!/usr/bin/env python3
"""Make coaching-non-rotated/*.pbn files compatible with bridge-classroom.com.

bridge-classroom is Rick Wilson's "dumb renderer" teaching platform
(github.com/Rick-Wilson/Bridge-Classroom): it reads a PBN and follows the
embedded coaching directives literally, with no inference. To render cleanly
there, each coached board needs:

  1. No pre-auction ``{...}`` comment blocks.  The ``{Shape ...}``/``{HCP ...}``/
     ``{Losers ...}`` stats and any ``{Curate ...}`` metadata are authoring/curation
     aids the Bridge Play Trainer ignores; bridge-classroom should not see them.
  2. Sequential board numbers.  ``[Board]`` is renumbered 1..n in file order.
  3. The source board number preserved in a separate ``[OriginalBoard]`` tag
     (inserted only if absent, so it captures the number once and survives reruns).
  4. The post-auction coaching ``{...}`` block to open by revealing the student's
     hand.  If the block has no leading ``[show ...]`` directive, ``[show S]`` is
     prepended (matching the hand-tuned model board in Basic_Major.pbn).

The model for the transform is the first board of
``coaching-non-rotated/Basic_Major.pbn``.

The script edits files **in place** under ``coaching-non-rotated/`` and is
idempotent: a second run is a no-op. Run from the project root:

    python3 -P py/bridge_classroom.py              # all *.pbn
    python3 -P py/bridge_classroom.py Basic_Major  # one (with or without .pbn)
    python3 -P py/bridge_classroom.py --check       # dry run, report only

(``-P`` keeps py/'s ``select.py`` from shadowing the stdlib.)
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COACHING_DIR = ROOT / "coaching-non-rotated"


def split_boards(text):
    """Split a PBN into per-board text chunks.

    A board starts at an ``[Event ...]`` tag at the start of a line. We split on
    that tag rather than tracking ``{}`` depth, so a board with an unbalanced
    coaching block (the known ``}}`` defect in some files) can't merge into its
    neighbour. ``[Event`` never appears inside coaching prose.
    """
    parts = re.split(r"(?m)(?=^\[Event\b)", text)
    return [p.rstrip("\n") for p in parts if p.strip()]


# A coaching/comment block: from the first '{' to the first '}'. Prose carries no
# nested braces, so non-greedy + DOTALL captures exactly one block and leaves any
# stray trailing '}' (the defect) outside the match, to be cleaned separately.
_BLOCK = re.compile(r"\{.*?\}", re.DOTALL)


def transform_board(text, seq):
    """Return (new_text, stats) for one board renumbered to ``seq``."""
    stats = {"stripped": 0, "show_added": False, "orig_added": False,
             "brace_fixed": False, "folded": 0, "fold_flagged": 0,
             "fold_unmatched": 0}

    m = re.search(r"(?m)^\[Auction\b.*$", text)
    if m is None:
        # No auction — not a coached board. Renumber only, leave the rest as-is.
        return _renumber(text, seq, stats), stats

    pre = text[: m.start()]
    post = text[m.start():]  # [Auction tag + call lines + coaching block + tail

    # 1. Drop every pre-auction {...} block (Shape/HCP/Losers, Curate, ...),
    #    consuming the block's own trailing newline so no blank gap is left.
    pre, n = _BLOCK.subn("", pre)
    pre = re.sub(r"\n[ \t]*(?=\n)", "", pre)  # squeeze any blank lines left behind
    stats["stripped"] = len(re.findall(r"\{", text[: m.start()]))

    # 2. In the auction-onward part, fix up the single coaching block.
    bm = _BLOCK.search(post)
    if bm:
        head = post[: bm.start()]          # [Auction tag + call lines
        block, added = _ensure_show_s(bm.group())
        stats["show_added"] = added
        tail = post[bm.end():]             # may start with a stray '}' (the defect)
        cleaned_tail = re.sub(r"^[ \t}]*\n?", "", tail)
        if cleaned_tail != re.sub(r"^[ \t]*\n?", "", tail):
            stats["brace_fixed"] = True
        post = head + block + ("\n" + cleaned_tail if cleaned_tail else "")

    text = _renumber(pre + post, seq, stats)
    return _fold_partner_bids(text, stats), stats


_BID_TAG = re.compile(r"\[BID\s+([^\]]+)\]", re.IGNORECASE)


def _seat_order(dealer):
    s = ["N", "E", "S", "W"]
    i = s.index(dealer)
    return s[i:] + s[:i]


def _norm_call(c):
    c = c.upper().strip()
    for nt in ("1NT", "2NT", "3NT", "4NT", "5NT", "6NT", "7NT"):
        c = c.replace(nt, nt[:-1])  # 1NT -> 1N
    return c


def _fold_partner_bids(text, stats, student="S"):
    """Keep `[BID]` anchors only for the student's own calls.

    bridge-classroom's renderer assumes every `[BID]` step is a student call:
    it auto-plays the auction until a student-seat call matches the *next*
    `[BID]`'s bid, so a `[BID]` on a partner/opponent call makes it skip past —
    and auto-play — the student's own later calls. So for each `[BID]` whose
    auction call belongs to a non-student seat, drop the marker and fold its
    prose into the preceding student chunk (the Basic_Major board-1 model).

    Each `[BID]` is mapped to a call the way the renderers anchor: walk the
    auction left-to-right and consume the next call whose value matches the
    `[BID]`'s bid. This handles boards where only some calls are anchored.

    Guards (leave the `[BID]` in place, counted separately, rather than risk a
    wrong edit): a value that matches no remaining call (`fold_unmatched`), or a
    non-student `[BID]` with no preceding student `[BID]` yet (`fold_flagged`).
    """
    am = re.search(r'(?m)^\[Auction "([^"]*)"\]$', text)
    if not am or am.group(1) not in "NESW":
        return text
    order = _seat_order(am.group(1))

    calls = []
    for line in text[am.end():].splitlines():
        s = line.strip()
        if s.startswith("[") or s.startswith("{"):
            break
        calls.append(line)
    tokens = " ".join(c.strip() for c in calls).split()
    callvals = [_norm_call(t) for t in tokens]
    callseats = [order[i % 4] for i in range(len(tokens))]

    bm = _BLOCK.search(text, am.end())
    if not bm:
        return text
    parts = re.split(r"(\[BID\s+[^\]]+\])", bm.group()[1:-1])

    out = parts[0]
    kept_student = False
    p = 0          # auction cursor for value-based matching
    i = 1
    while i < len(parts):
        tag, txt = parts[i], parts[i + 1] if i + 1 < len(parts) else ""
        val = _norm_call(_BID_TAG.match(tag).group(1))
        j = p
        while j < len(callvals) and callvals[j] != val:
            j += 1
        seat = callseats[j] if j < len(callvals) else None
        if seat is not None:
            p = j + 1
        if seat == student:
            out += tag + txt
            kept_student = True
        elif seat is not None and kept_student:
            merged = txt.lstrip()
            out = (out.rstrip() + " " + merged) if merged else out + txt
            stats["folded"] += 1
        else:
            out += tag + txt          # unmatched, or no preceding student chunk
            stats["fold_unmatched" if seat is None else "fold_flagged"] += 1
        i += 2

    return text[: bm.start()] + "{" + out + "}" + text[bm.end():]


def _ensure_show_s(block):
    """Prepend ``[show S]`` to a coaching block unless it already leads with a
    ``[show ...]`` directive."""
    after = block[1:]
    if after.lstrip().lower().startswith("[show"):
        return block, False
    return "{[show S]" + block[1:], True


def _renumber(text, seq, stats):
    """Renumber ``[Board]`` to ``seq`` and insert ``[OriginalBoard]`` if absent."""
    bm = re.search(r'(?m)^\[Board "([^"]*)"\]', text)
    if bm is None:
        return text
    orig = bm.group(1)
    text = text[: bm.start()] + f'[Board "{seq}"]' + text[bm.end():]
    if not re.search(r"(?m)^\[OriginalBoard ", text):
        bm = re.search(r'(?m)^\[Board "[^"]*"\]', text)
        text = text[: bm.end()] + f'\n[OriginalBoard "{orig}"]' + text[bm.end():]
        stats["orig_added"] = True
    return text


def transform_file(path, check):
    text = path.read_text()
    boards = split_boards(text)

    new_boards = []
    totals = {"stripped": 0, "show_added": 0, "orig_added": 0, "brace_fixed": 0,
              "folded": 0, "fold_flagged": 0, "fold_unmatched": 0}
    for seq, board in enumerate(boards, start=1):
        new_board, stats = transform_board(board, seq)
        new_boards.append(new_board)
        for k in totals:
            totals[k] += int(stats[k])

    out_text = "\n\n".join(b.rstrip("\n") for b in new_boards) + "\n"
    changed = out_text != text
    if changed and not check:
        path.write_text(out_text)
    return changed, len(boards), totals


def resolve_targets(names):
    if not names:
        return sorted(COACHING_DIR.glob("*.pbn"))
    targets = []
    for n in names:
        p = COACHING_DIR / (n if n.endswith(".pbn") else f"{n}.pbn")
        if not p.exists():
            sys.exit(f"error: {p} not found")
        targets.append(p)
    return targets


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios", nargs="*",
                    help="scenario name(s) under coaching-non-rotated/ (default: all)")
    ap.add_argument("--check", action="store_true",
                    help="report what would change without writing")
    args = ap.parse_args()

    any_changed = False
    for path in resolve_targets(args.scenarios):
        changed, n_boards, t = transform_file(path, args.check)
        any_changed = any_changed or changed
        verb = "would update" if (changed and args.check) else \
               ("updated" if changed else "ok")
        extra = ""
        if t["brace_fixed"]:
            extra += f", {t['brace_fixed']} stray-brace fixed"
        if t["folded"]:
            extra += f", {t['folded']} partner-[BID] folded"
        if t["fold_flagged"]:
            extra += f", {t['fold_flagged']} FLAGGED (non-student [BID], no preceding student chunk)"
        if t["fold_unmatched"]:
            extra += f", {t['fold_unmatched']} FLAGGED ([BID] matches no auction call)"
        detail = (f"  ({t['stripped']} blocks stripped, "
                  f"{t['orig_added']} OriginalBoard added, "
                  f"{t['show_added']} show-S added{extra})") if changed else ""
        print(f"{verb:>12}  {path.name}  [{n_boards} boards]{detail}")

    if args.check and any_changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
