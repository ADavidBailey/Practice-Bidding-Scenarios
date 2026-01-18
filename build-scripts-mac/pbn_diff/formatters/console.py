"""
Console output formatter with ANSI colors.
"""

from typing import List, Optional

from ..comparator import DiffResult, DiffType, RecordDifference


class ConsoleFormatter:
    """Format diff results for console output."""

    # ANSI color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, use_color: bool = True):
        self.use_color = use_color

    def _color(self, text: str, color: str) -> str:
        """Apply color if enabled."""
        if self.use_color:
            return f"{color}{text}{self.RESET}"
        return text

    def format_summary(self, result: DiffResult) -> str:
        """Format summary statistics."""
        lines = []
        lines.append(f"{self._color('PBN Comparison Summary', self.BOLD)}")
        lines.append(f"  File 1: {result.file1_path}")
        lines.append(f"  File 2: {result.file2_path}")
        lines.append(f"  Mode: {result.mode}")
        lines.append("")
        lines.append(f"  Records in file 1: {result.total_records_file1}")
        lines.append(f"  Records in file 2: {result.total_records_file2}")

        if result.mode == "semantic":
            lines.append(f"  Matched records:   {result.matched_records}")

            if result.modified_records:
                lines.append(
                    self._color(
                        f"  Modified records:  {result.modified_records}", self.YELLOW
                    )
                )
            else:
                lines.append(f"  Modified records:  {result.modified_records}")

        if result.added_records:
            lines.append(
                self._color(f"  Added records:     {result.added_records}", self.GREEN)
            )
        else:
            lines.append(f"  Added records:     {result.added_records}")

        if result.removed_records:
            lines.append(
                self._color(f"  Removed records:   {result.removed_records}", self.RED)
            )
        else:
            lines.append(f"  Removed records:   {result.removed_records}")

        return "\n".join(lines)

    def format_differences(
        self,
        result: DiffResult,
        board_filter: Optional[List[int]] = None,
        head_limit: int = 0,
    ) -> str:
        """Format detailed differences."""
        lines = []
        count = 0

        for diff in result.record_differences:
            # Apply board filter
            if board_filter and diff.board_number not in board_filter:
                continue

            # Apply head limit
            if head_limit > 0 and count >= head_limit:
                remaining = len(result.record_differences) - count
                lines.append("")
                lines.append(
                    self._color(f"... and {remaining} more differences (use --head 0 to show all)", self.CYAN)
                )
                break
            count += 1

            # Format record header
            if diff.diff_type == DiffType.ADDED:
                header = self._color(
                    f"[+] Board {diff.board_number} (ADDED)", self.GREEN
                )
            elif diff.diff_type == DiffType.REMOVED:
                header = self._color(
                    f"[-] Board {diff.board_number} (REMOVED)", self.RED
                )
            else:
                header = self._color(
                    f"[~] Board {diff.board_number} (MODIFIED)", self.YELLOW
                )

            lines.append("")
            lines.append(header)

            # Truncate deal for display
            deal_display = diff.deal
            if len(deal_display) > 60:
                deal_display = deal_display[:57] + "..."
            lines.append(f"    Deal: {deal_display}")

            # Format tag differences
            for tag_diff in diff.tag_differences:
                if tag_diff.diff_type == DiffType.ADDED:
                    lines.append(
                        self._color(
                            f"    + [{tag_diff.tag_name}]: {tag_diff.value2}",
                            self.GREEN,
                        )
                    )
                elif tag_diff.diff_type == DiffType.REMOVED:
                    lines.append(
                        self._color(
                            f"    - [{tag_diff.tag_name}]: {tag_diff.value1}", self.RED
                        )
                    )
                else:
                    lines.append(
                        self._color(f"    ~ [{tag_diff.tag_name}]:", self.YELLOW)
                    )
                    lines.append(self._color(f"        - {tag_diff.value1}", self.RED))
                    lines.append(
                        self._color(f"        + {tag_diff.value2}", self.GREEN)
                    )

        return "\n".join(lines)

    def format(
        self,
        result: DiffResult,
        summary_only: bool = False,
        board_filter: Optional[List[int]] = None,
        head_limit: int = 0,
    ) -> str:
        """Format complete output."""
        output = self.format_summary(result)

        if not summary_only and result.record_differences:
            output += "\n" + self.format_differences(result, board_filter, head_limit)

        return output
