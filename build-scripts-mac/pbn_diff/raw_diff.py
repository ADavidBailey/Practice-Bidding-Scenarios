"""
Raw text diff for PBN files using Python's difflib.
"""

import difflib
import re
from typing import List, Optional

from .comparator import DiffResult


# Default patterns to filter out in raw diff mode (simple prefix matches)
DEFAULT_RAW_FILTERS = [
    "[Event",
    "[Date",
    "% Time needed",
]

# Regex patterns for more complex filtering
# Matches: % followed by any characters, then [Event (dealer bug produces stray E/O/F chars)
DEFAULT_RAW_REGEX_FILTERS = [
    re.compile(r"^%.*\[Event"),
]


def _should_filter_line(line: str, filters: List[str]) -> bool:
    """Check if a line should be filtered out."""
    stripped = line.strip()

    # Check simple prefix patterns
    for pattern in filters:
        if stripped.startswith(pattern):
            return True

    # Check regex patterns
    for regex in DEFAULT_RAW_REGEX_FILTERS:
        if regex.search(stripped):
            return True

    return False


def raw_diff(
    file1_path: str,
    file2_path: str,
    context_lines: int = 3,
    ignore_comments: bool = False,
    apply_raw_filter: bool = True,
) -> DiffResult:
    """
    Perform a raw text diff between two PBN files.

    Args:
        file1_path: Path to first file
        file2_path: Path to second file
        context_lines: Number of context lines in unified diff
        ignore_comments: If True, skip lines starting with %
        apply_raw_filter: If True, filter out [Event, [Date, % Time needed lines

    Returns:
        DiffResult with raw_diff_lines populated
    """
    with open(file1_path, "r", encoding="utf-8", errors="replace") as f:
        lines1 = f.readlines()

    with open(file2_path, "r", encoding="utf-8", errors="replace") as f:
        lines2 = f.readlines()

    # Optionally filter comments
    if ignore_comments:
        lines1 = [line for line in lines1 if not line.strip().startswith("%")]
        lines2 = [line for line in lines2 if not line.strip().startswith("%")]

    # Apply default raw filters (Event, Date, Time needed)
    if apply_raw_filter:
        lines1 = [line for line in lines1 if not _should_filter_line(line, DEFAULT_RAW_FILTERS)]
        lines2 = [line for line in lines2 if not _should_filter_line(line, DEFAULT_RAW_FILTERS)]

    # Generate unified diff
    diff = list(
        difflib.unified_diff(
            lines1,
            lines2,
            fromfile=file1_path,
            tofile=file2_path,
            n=context_lines,
        )
    )

    # Count differences for summary
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    return DiffResult(
        file1_path=file1_path,
        file2_path=file2_path,
        mode="raw",
        total_records_file1=_count_boards(lines1),
        total_records_file2=_count_boards(lines2),
        matched_records=0,
        modified_records=0,
        added_records=added,
        removed_records=removed,
        record_differences=[],
        comment_differences=[],
        raw_diff_lines=diff,
    )


def _count_boards(lines: List[str]) -> int:
    """Count number of [Board tags in lines."""
    return sum(1 for line in lines if line.strip().startswith("[Board"))


def format_raw_diff(
    diff_lines: List[str], use_color: bool = True, head_limit: int = 0
) -> str:
    """
    Format raw diff lines with optional ANSI colors.

    Args:
        diff_lines: Lines from unified_diff
        use_color: Whether to add ANSI color codes
        head_limit: Limit output to first N hunks (0 = no limit)

    Returns:
        Formatted string
    """
    RED = "\033[91m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    # Split diff into hunks (each starting with @@)
    hunks: List[List[str]] = []
    current_hunk: List[str] = []
    header_lines: List[str] = []

    for line in diff_lines:
        if line.startswith("@@"):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = [line]
        elif line.startswith("---") or line.startswith("+++"):
            header_lines.append(line)
        elif current_hunk:
            current_hunk.append(line)

    if current_hunk:
        hunks.append(current_hunk)

    # Apply head limit
    total_hunks = len(hunks)
    truncated = False
    if head_limit > 0 and total_hunks > head_limit:
        hunks = hunks[:head_limit]
        truncated = True

    # Format output
    result = []

    # Add header lines
    for line in header_lines:
        if use_color:
            result.append(f"{CYAN}{line}{RESET}")
        else:
            result.append(line)

    # Add hunks
    for hunk in hunks:
        for line in hunk:
            if not use_color:
                result.append(line)
            elif line.startswith("@@"):
                result.append(f"{CYAN}{line}{RESET}")
            elif line.startswith("+"):
                result.append(f"{GREEN}{line}{RESET}")
            elif line.startswith("-"):
                result.append(f"{RED}{line}{RESET}")
            else:
                result.append(line)

    # Add truncation message
    if truncated:
        remaining = total_hunks - head_limit
        msg = f"\n... and {remaining} more diff hunks (use --head 0 for all)\n"
        if use_color:
            result.append(f"{YELLOW}{msg}{RESET}")
        else:
            result.append(msg)

    return "".join(result)
