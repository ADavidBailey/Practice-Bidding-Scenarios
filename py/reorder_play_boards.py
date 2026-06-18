#!/usr/bin/env python3
"""Reorder a play-coaching .pbn so the first 3 boards are middle-of-the-road
(class: intended at the file's modal difficulty) and the rest are randomized,
then renumber [Board] 1..N preserving the old value as [OriginalBoard].

Randomization is seeded by scenario name so runs are reproducible.
Usage: python3 -P py/reorder_play_boards.py <file.pbn> [<file.pbn> ...]
"""
import re
import sys
import random
from collections import Counter
from pathlib import Path


def split_boards(text):
    """Return (preamble, [board_text, ...]). Each board starts at '[Event'."""
    idxs = [m.start() for m in re.finditer(r'(?m)^\[Event ', text)]
    if not idxs:
        return text, []
    preamble = text[:idxs[0]]
    bounds = idxs + [len(text)]
    boards = [text[bounds[i]:bounds[i + 1]] for i in range(len(idxs))]
    return preamble, boards


def field(board, key):
    m = re.search(r'(?m)^%s:\s*(.+)$' % re.escape(key), board)
    return m.group(1).strip() if m else None


def board_num(board):
    m = re.search(r'(?m)^\[Board\s+"([^"]*)"\]', board)
    return m.group(1) if m else None


def reorder(text, seed):
    preamble, boards = split_boards(text)
    if not boards:
        raise SystemExit("no boards found")

    rng = random.Random(seed)

    intended = [b for b in boards if field(b, 'class') == 'intended']
    pool = intended if intended else boards
    diffs = [field(b, 'difficulty') for b in pool]
    modal = Counter(d for d in diffs if d is not None).most_common(1)[0][0]
    mid_pool = [b for b in pool if field(b, 'difficulty') == modal]

    if len(mid_pool) < 3:
        # top up from the rest of the intended/whole pool to guarantee 3
        extra = [b for b in pool if b not in mid_pool]
        rng.shuffle(extra)
        mid_pool = mid_pool + extra

    rng.shuffle(mid_pool)
    middle3 = mid_pool[:3]

    rest = [b for b in boards if b not in middle3]
    rng.shuffle(rest)

    ordered = middle3 + rest
    assert len(ordered) == len(boards)

    out = []
    for pos, b in enumerate(ordered, start=1):
        orig = board_num(b)
        # renumber [Board] to position, insert [OriginalBoard] right after it
        b = re.sub(r'(?m)^\[Board\s+"[^"]*"\]',
                   '[Board "%d"]\n[OriginalBoard "%s"]' % (pos, orig),
                   b, count=1)
        out.append(b)

    return preamble + ''.join(out)


def main():
    for path in sys.argv[1:]:
        p = Path(path)
        text = p.read_text()
        if '[OriginalBoard' in text:
            print("SKIP (already reordered): %s" % p.name)
            continue
        new = reorder(text, seed=p.stem)
        p.write_text(new)
        nb = len(split_boards(new)[1])
        print("reordered %-34s (%d boards)" % (p.name, nb))


if __name__ == '__main__':
    main()
