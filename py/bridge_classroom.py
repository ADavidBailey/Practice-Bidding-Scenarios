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
             "brace_fixed": False}

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

    return _renumber(pre + post, seq, stats), stats


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
    totals = {"stripped": 0, "show_added": 0, "orig_added": 0, "brace_fixed": 0}
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
        brace = f", {t['brace_fixed']} stray-brace fixed" if t["brace_fixed"] else ""
        detail = (f"  ({t['stripped']} blocks stripped, "
                  f"{t['orig_added']} OriginalBoard added, "
                  f"{t['show_added']} show-S added{brace})") if changed else ""
        print(f"{verb:>12}  {path.name}  [{n_boards} boards]{detail}")

    if args.check and any_changed:
        sys.exit(1)


if __name__ == "__main__":
    main()
