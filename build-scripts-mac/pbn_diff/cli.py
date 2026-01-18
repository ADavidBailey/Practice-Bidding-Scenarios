"""
CLI entry point for PBN diff tool.
"""

import argparse
import glob
import os
import sys
from typing import List, Optional

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pbn_diff.comparator import SemanticComparator
from pbn_diff.cross_stage import CrossStageComparator, STAGE_TO_FOLDER_KEY
from pbn_diff.formatters.console import ConsoleFormatter
from pbn_diff.formatters.html import HTMLFormatter
from pbn_diff.git_integration import GitIntegration, find_repo_root
from pbn_diff.parser import PBNParser
from pbn_diff.raw_diff import raw_diff, format_raw_diff


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="PBN file comparison tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Compare two files semantically
    python pbn-diff.py bba/1N.pbn bba-old/1N.pbn

    # Raw text diff
    python pbn-diff.py file1.pbn file2.pbn --raw

    # Compare local changes against git HEAD
    python pbn-diff.py bba/1N.pbn --git

    # Compare against specific commit
    python pbn-diff.py bba/1N.pbn --git --commit HEAD~5

    # Cross-stage comparison
    python pbn-diff.py 1N --cross-stage pbn bba

    # Generate HTML report
    python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --output html -o diff.html

    # Summary only
    python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --summary

    # Compare only specific tags
    python pbn-diff.py bba/1N.pbn bba-old/1N.pbn --tags Deal,Contract,Auction
        """,
    )

    # Positional arguments
    parser.add_argument("file1", nargs="?", help="First PBN file or scenario name (for --cross-stage)")
    parser.add_argument("file2", nargs="?", help="Second PBN file (not needed with --git or --cross-stage)")

    # Comparison type (raw vs semantic)
    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument(
        "--raw", action="store_true", help="Raw text diff (line-by-line)"
    )
    type_group.add_argument(
        "--semantic",
        action="store_true",
        help="Semantic diff (default) - structure-aware comparison",
    )

    # Source mode (git, cross-stage, or two files)
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--git", action="store_true", help="Compare against git version"
    )
    source_group.add_argument(
        "--cross-stage",
        nargs=2,
        metavar=("STAGE1", "STAGE2"),
        help="Compare across pipeline stages (e.g., pbn bba)",
    )

    # Git options
    parser.add_argument(
        "--commit", default="HEAD", help="Git commit reference (default: HEAD)"
    )

    # Output options
    parser.add_argument(
        "--output",
        choices=["console", "html"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "-o", "--output-file", help="Write output to file (required for html)"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI colors in console output"
    )

    # Filtering options
    parser.add_argument(
        "--tags", help="Only compare specific tags (comma-separated)"
    )
    parser.add_argument(
        "--ignore-tags", help="Ignore specific tags (comma-separated)"
    )
    parser.add_argument(
        "--ignore-comments",
        action="store_true",
        help="Ignore comments in raw diff",
    )
    parser.add_argument(
        "--no-raw-filter",
        action="store_true",
        help="Disable default raw diff filtering (Event, Date, Time needed lines)",
    )
    parser.add_argument(
        "--board",
        type=int,
        action="append",
        help="Only show specific board(s) - can be used multiple times",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show only summary statistics"
    )
    parser.add_argument(
        "--head",
        type=int,
        default=5,
        help="Limit output: first N boards (semantic) or N diff hunks (raw). Default: 5, use 0 for all",
    )
    parser.add_argument(
        "--files-head",
        type=int,
        default=10,
        help="Limit number of mismatched files shown in detail (default: 10, use 0 for all)",
    )

    # Verbosity
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Minimal output (exit code only)"
    )

    # List stages
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="List available pipeline stages and exit",
    )

    return parser.parse_args(args)


def resolve_path(path: str, project_root: str) -> str:
    """Resolve path relative to project root if not absolute."""
    if os.path.isabs(path):
        return path
    return os.path.join(project_root, path)


def expand_glob(pattern: str, project_root: str) -> List[str]:
    """Expand a glob pattern to list of files."""
    resolved = resolve_path(pattern, project_root)
    files = glob.glob(resolved)
    return sorted(files)


def is_glob_pattern(path: str) -> bool:
    """Check if path contains glob wildcards."""
    return '*' in path or '?' in path or '[' in path


def run_multi_file_git_comparison(
    parsed_args: argparse.Namespace,
    project_root: str,
    pbn_parser: PBNParser,
    comparator: SemanticComparator,
) -> int:
    """
    Run git comparison on multiple files matching a glob pattern.
    Returns exit code: 0 if all match, 1 if any differ, 2 on error.
    """
    # Find repo root first
    repo_root = (
        find_repo_root(os.getcwd())
        or find_repo_root(project_root)
    )
    if not repo_root:
        print("Error: Not in a git repository")
        return 2

    git = GitIntegration(repo_root)
    formatter = ConsoleFormatter(use_color=not parsed_args.no_color)

    # Expand glob pattern to get all matching files
    all_files = expand_glob(parsed_args.file1, project_root)
    if not all_files:
        print(f"Error: No files match pattern: {parsed_args.file1}")
        return 2

    # Use git to quickly identify which files have actually changed
    changed_files_rel = set(git.get_changed_files(parsed_args.commit, parsed_args.file1))

    # Filter to only files that git says have changed
    files_to_check = []
    unchanged_count = 0
    for file_path in all_files:
        rel_path = os.path.relpath(file_path, repo_root)
        if rel_path in changed_files_rel:
            files_to_check.append(file_path)
        else:
            unchanged_count += 1

    # Track statistics
    total_files = len(all_files)
    matched_files = unchanged_count  # Files git says are unchanged
    mismatched_files = 0
    error_files = 0
    mismatched_details = []

    # Only process files that git identified as changed
    for file_path in files_to_check:
        rel_path = os.path.relpath(file_path, project_root)

        # Get committed version
        temp_path = git.get_file_at_commit(file_path, parsed_args.commit)
        if not temp_path:
            # File doesn't exist in git - skip or count as error
            error_files += 1
            continue

        try:
            if parsed_args.raw:
                result = raw_diff(
                    temp_path, file_path,
                    ignore_comments=parsed_args.ignore_comments,
                    apply_raw_filter=not parsed_args.no_raw_filter,
                )
            else:
                file1 = pbn_parser.parse_file(temp_path)
                file2 = pbn_parser.parse_file(file_path)
                result = comparator.compare(file1, file2)
                result.file1_path = f"{rel_path} ({parsed_args.commit})"
                result.file2_path = f"{rel_path} (working copy)"

            if result.has_differences:
                mismatched_files += 1
                mismatched_details.append((rel_path, result))
            else:
                matched_files += 1

        except Exception as e:
            error_files += 1
            if parsed_args.verbose:
                print(f"Error processing {rel_path}: {e}")
        finally:
            os.unlink(temp_path)

    # Print summary
    print(formatter._color("Multi-File Git Comparison Summary", formatter.BOLD))
    print(f"  Pattern: {parsed_args.file1}")
    print(f"  Commit: {parsed_args.commit}")
    print(f"  Files checked: {total_files}")
    print(formatter._color(f"  Matched: {matched_files}", formatter.GREEN) if matched_files else f"  Matched: {matched_files}")
    if mismatched_files:
        print(formatter._color(f"  Mismatched: {mismatched_files}", formatter.RED))
    else:
        print(f"  Mismatched: {mismatched_files}")
    if error_files:
        print(formatter._color(f"  Errors/skipped: {error_files}", formatter.YELLOW))

    # Print details for mismatched files
    if mismatched_details and not parsed_args.summary:
        files_to_show = mismatched_details
        if parsed_args.files_head > 0:
            files_to_show = mismatched_details[:parsed_args.files_head]

        for rel_path, result in files_to_show:
            print()
            print(formatter._color(f"=== {rel_path} ===", formatter.BOLD))
            # Print compact summary for this file
            print(f"  Records: {result.total_records_file1} vs {result.total_records_file2}")
            if result.matched_records:
                print(f"  Matched: {result.matched_records}")
            if result.modified_records:
                print(formatter._color(f"  Modified: {result.modified_records}", formatter.YELLOW))
            if result.added_records:
                print(formatter._color(f"  Added: {result.added_records}", formatter.GREEN))
            if result.removed_records:
                print(formatter._color(f"  Removed: {result.removed_records}", formatter.RED))
            # Show detailed differences
            diff_output = formatter.format_differences(
                result,
                board_filter=parsed_args.board,
                head_limit=parsed_args.head,
            )
            if diff_output.strip():
                print(diff_output)

        if parsed_args.files_head > 0 and len(mismatched_details) > parsed_args.files_head:
            remaining = len(mismatched_details) - parsed_args.files_head
            print()
            print(formatter._color(
                f"... and {remaining} more mismatched files (use --files-head 0 to show all)",
                formatter.CYAN
            ))

    return 1 if mismatched_files > 0 else 0


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parsed_args = parse_args(args)

    # Import config (may fail if env vars not set, so do it late)
    try:
        from config import PROJECT_ROOT, FOLDERS
    except SystemExit:
        # Config validation failed - use fallback for standalone operation
        PROJECT_ROOT = find_repo_root(os.getcwd()) or os.getcwd()
        FOLDERS = {
            "pbn": os.path.join(PROJECT_ROOT, "pbn"),
            "bba": os.path.join(PROJECT_ROOT, "bba"),
            "bba_filtered": os.path.join(PROJECT_ROOT, "bba-filtered"),
            "bba_filtered_out": os.path.join(PROJECT_ROOT, "bba-filtered-out"),
            "bidding_sheets": os.path.join(PROJECT_ROOT, "bidding-sheets"),
            "pbn_rotated": os.path.join(PROJECT_ROOT, "pbn-rotated-for-4-players"),
        }

    # Handle --list-stages
    if parsed_args.list_stages:
        print("Available pipeline stages:")
        for stage in sorted(set(STAGE_TO_FOLDER_KEY.keys())):
            folder_key = STAGE_TO_FOLDER_KEY[stage]
            folder = FOLDERS.get(folder_key, "not configured")
            print(f"  {stage:20} -> {folder}")
        return 0

    # Validate file1 is provided for actual comparisons
    if not parsed_args.file1:
        print("Error: file1 is required (or use --list-stages)")
        return 2

    # Parse tag filters
    compare_tags = parsed_args.tags.split(",") if parsed_args.tags else None
    ignore_tags = parsed_args.ignore_tags.split(",") if parsed_args.ignore_tags else None

    pbn_parser = PBNParser()
    comparator = SemanticComparator(compare_tags=compare_tags, ignore_tags=ignore_tags)

    try:
        # Determine comparison mode and get result
        if parsed_args.cross_stage:
            # Cross-stage comparison
            stage_comparator = CrossStageComparator(PROJECT_ROOT, FOLDERS)
            result = stage_comparator.compare_stages(
                parsed_args.file1,
                parsed_args.cross_stage[0],
                parsed_args.cross_stage[1],
                comparator,
                pbn_parser,
            )
        elif parsed_args.git:
            # Git comparison - check for wildcard
            if is_glob_pattern(parsed_args.file1):
                try:
                    return run_multi_file_git_comparison(
                        parsed_args, PROJECT_ROOT, pbn_parser, comparator
                    )
                except Exception as e:
                    print(f"Error: {e}")
                    if parsed_args.verbose:
                        import traceback
                        traceback.print_exc()
                    return 2

            # Single file git comparison
            file_path = resolve_path(parsed_args.file1, PROJECT_ROOT)

            # Find repo from file location, then cwd, then PROJECT_ROOT
            repo_root = (
                find_repo_root(os.path.dirname(file_path))
                or find_repo_root(os.getcwd())
                or find_repo_root(PROJECT_ROOT)
            )
            if not repo_root:
                print("Error: Not in a git repository")
                return 2

            git = GitIntegration(repo_root)

            if not os.path.exists(file_path):
                print(f"Error: File not found: {file_path}")
                return 2

            temp_path = git.get_file_at_commit(file_path, parsed_args.commit)
            if not temp_path:
                print(f"Error: File not found at {parsed_args.commit}: {parsed_args.file1}")
                return 1

            try:
                if parsed_args.raw:
                    result = raw_diff(
                        temp_path, file_path,
                        ignore_comments=parsed_args.ignore_comments,
                        apply_raw_filter=not parsed_args.no_raw_filter,
                    )
                else:
                    file1 = pbn_parser.parse_file(temp_path)
                    file2 = pbn_parser.parse_file(file_path)
                    result = comparator.compare(file1, file2)
                    # Update paths for display
                    result.file1_path = f"{parsed_args.file1} ({parsed_args.commit})"
                    result.file2_path = f"{parsed_args.file1} (working copy)"
            finally:
                # Clean up temp file
                os.unlink(temp_path)

        elif parsed_args.raw:
            # Raw diff
            if not parsed_args.file2:
                print("Error: Raw diff requires two files")
                return 2
            file1_path = resolve_path(parsed_args.file1, PROJECT_ROOT)
            file2_path = resolve_path(parsed_args.file2, PROJECT_ROOT)
            result = raw_diff(
                file1_path, file2_path,
                ignore_comments=parsed_args.ignore_comments,
                apply_raw_filter=not parsed_args.no_raw_filter,
            )
        else:
            # Semantic diff (default)
            if not parsed_args.file2:
                print("Error: Semantic diff requires two files (or use --git)")
                return 2
            file1_path = resolve_path(parsed_args.file1, PROJECT_ROOT)
            file2_path = resolve_path(parsed_args.file2, PROJECT_ROOT)

            if not os.path.exists(file1_path):
                print(f"Error: File not found: {file1_path}")
                return 2
            if not os.path.exists(file2_path):
                print(f"Error: File not found: {file2_path}")
                return 2

            file1 = pbn_parser.parse_file(file1_path)
            file2 = pbn_parser.parse_file(file2_path)
            result = comparator.compare(file1, file2)

        # Handle quiet mode
        if parsed_args.quiet:
            return 1 if result.has_differences else 0

        # Format output
        if parsed_args.output == "html":
            formatter = HTMLFormatter()
            output = formatter.format(result, parsed_args.board)
        elif result.mode == "raw" and result.raw_diff_lines is not None:
            # Raw diff formatting
            output = format_raw_diff(
                result.raw_diff_lines, not parsed_args.no_color, parsed_args.head
            )
        else:
            formatter = ConsoleFormatter(use_color=not parsed_args.no_color)
            output = formatter.format(
                result,
                summary_only=parsed_args.summary,
                board_filter=parsed_args.board,
                head_limit=parsed_args.head,
            )

        # Write output
        if parsed_args.output_file:
            with open(parsed_args.output_file, "w", encoding="utf-8") as f:
                f.write(output)
            if not parsed_args.quiet:
                print(f"Output written to: {parsed_args.output_file}")
        else:
            print(output)

        # Return exit code
        return 1 if result.has_differences else 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 2
    except ValueError as e:
        print(f"Error: {e}")
        return 2
    except Exception as e:
        print(f"Error: {e}")
        if parsed_args.verbose:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
