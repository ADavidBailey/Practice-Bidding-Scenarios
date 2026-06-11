#!/usr/bin/env python3
"""promote.py — gated promotion of coaching-curated/ -> coaching/ (served).

coaching-curated/ is the working/staging directory: prose is authored there and
the gates run there. coaching/ is what the Bridge Play Trainer actually serves
(BRIDGE_DATA_ROOT/coaching/<scenario>.pbn). The two drift as curated content is
edited, so a scenario is only safe to serve once it passes the full gate suite:

  - coach.py validate   marker structure (intro/[BID]/[ACCEPT]/voice; [BID]
                        checks scoped to bidding lessons) PLUS the suit-quality
                        prose gate ('solid' only when the suit really is).
  - suit_quality        the issue-#29 ordering lint: a bidding lesson must not
                        serve a solid 6+-card suit in its first 4 boards.

A scenario that fails any gate is BLOCKED (left un-promoted) and reported with
its findings; nothing is copied unless its gate count is 0. The script prints
exactly what it promoted, what was already current, and what it blocked, and
exits non-zero if anything was blocked.

  python3 -P py/promote.py            # gate, then promote every curated scenario
  python3 -P py/promote.py --check    # gate only, copy nothing (dry run)
  python3 -P py/promote.py Scn1 Scn2  # restrict to the named scenarios
"""
import sys, os, glob, shutil, io, contextlib

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import coach
from suit_quality import solidity_violations, solid_suit_positions

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CURATED = os.path.join(ROOT, "coaching-curated")
SERVED = os.path.join(ROOT, "coaching")


def gate(scn):
    """Run the full gate suite against the CURATED copy of <scn>.

    Returns (ok, info). ok is True only when every gate reports zero findings.
    coach.validate already folds the suit-quality prose gate into its count, so
    the only thing it does not cover is the bidding-lesson ordering lint, which
    we add here."""
    path = os.path.join(CURATED, f"{scn}.pbn")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):       # silence validate's per-board log
        structure = coach.validate(scn)
    prose = len(solidity_violations(path))       # subset of `structure`; shown
    ordering = 0                                 # for transparency in reports
    if scn.startswith("Basic_"):
        ordering = sum(1 for pos, *_ in solid_suit_positions(path) if pos <= 4)
    ok = (structure == 0 and ordering == 0)
    return ok, {"structure": structure, "prose": prose, "ordering": ordering,
                "log": buf.getvalue().strip()}


def main(argv):
    flags = [a for a in argv if a.startswith("-")]
    names = [a for a in argv if not a.startswith("-")]
    check_only = "--check" in flags
    scns = names or sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(CURATED, "*.pbn")))

    promoted, current, blocked = [], [], []
    for scn in scns:
        cur = os.path.join(CURATED, f"{scn}.pbn")
        srv = os.path.join(SERVED, f"{scn}.pbn")
        if not os.path.exists(cur):
            blocked.append((scn, "no curated file"))
            continue
        ok, info = gate(scn)
        if not ok:
            reason = (f"{info['structure']} structure issue(s) "
                      f"(incl. {info['prose']} solid-prose), "
                      f"{info['ordering']} ordering")
            blocked.append((scn, reason))
            for line in info["log"].splitlines():
                print("    " + line)
            continue
        same = (os.path.exists(srv)
                and open(cur, "rb").read() == open(srv, "rb").read())
        if same:
            current.append(scn)
            continue
        if not check_only:
            shutil.copyfile(cur, srv)
        promoted.append(scn)

    verb = "WOULD PROMOTE" if check_only else "PROMOTED"
    print(f"\n{verb} ({len(promoted)}): " + (", ".join(promoted) or "none"))
    print(f"ALREADY CURRENT ({len(current)}): " + (", ".join(current) or "none"))
    print(f"BLOCKED ({len(blocked)}):" + (" none" if not blocked else ""))
    for scn, reason in blocked:
        print(f"  {scn}: {reason}")
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
