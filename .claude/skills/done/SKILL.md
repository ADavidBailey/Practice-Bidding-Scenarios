---
name: done
description: >
  End-of-session wrap-up. Save what was learned this session to auto-memory,
  verify the working tree is committed/pushed, and emit a brief resume prompt
  the user can paste next time. Invoke as /done to close a work session.
  Wrap-up is auto-memory ONLY — never writes a handoff.md or any handoff file.
---

# /done — close the session

Run the session wrap-up, briefly:

1. **Save durable learnings to auto-memory.** Scan this session for things worth
   remembering that are NOT already in memory and NOT derivable from the code, git
   history, or CLAUDE.md:
   - new/changed tooling and how to invoke it,
   - rules / preferences the user stated or confirmed (with the *why*),
   - ongoing project state and open items (convert relative dates to absolute),
   - non-obvious gotchas hit and how they were resolved.
   Write each as a memory file in the project's memory dir using the standard
   frontmatter, add a one-line `MEMORY.md` pointer, and link related notes with
   `[[name]]`. **Update an existing memory instead of duplicating; delete any that
   this session proved wrong.** Skip anything the repo already records.

2. **No handoff file.** Wrap-up is auto-memory only — do NOT create handoff.md or
   any session-handoff document (standing user preference).

3. **Check the tree.** Run `git status`. If there are uncommitted changes or
   unpushed commits, report them plainly. Do NOT auto-commit or push unless the
   user already authorized it this session ("commit" implies commit + push here).

4. **Emit a resume prompt.** Finish with a short (≈2–6 line) "resume prompt"
   capturing the current state and the top open / next items — phrased so the user
   can paste it at the start of the next session to pick up where they left off.

Keep the whole thing brief — this is a close-out, not a report.
