"""
Semantic comparison of PBN files.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from .parser import PBNFile, PBNRecord


class DiffType(Enum):
    """Types of differences detected."""

    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"


@dataclass
class TagDifference:
    """Difference in a single tag between two records."""

    tag_name: str
    diff_type: DiffType
    value1: Optional[str]  # Value in file1 (None if added)
    value2: Optional[str]  # Value in file2 (None if removed)


@dataclass
class RecordDifference:
    """Differences between two matched records."""

    board_number: int
    deal: str
    diff_type: DiffType  # MODIFIED, ADDED, REMOVED
    tag_differences: List[TagDifference] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.tag_differences) > 0 or self.diff_type != DiffType.UNCHANGED


@dataclass
class DiffResult:
    """Complete diff result between two PBN files."""

    file1_path: str
    file2_path: str
    mode: str  # "raw", "semantic"

    # Summary statistics
    total_records_file1: int = 0
    total_records_file2: int = 0
    matched_records: int = 0
    modified_records: int = 0
    added_records: int = 0  # In file2 but not file1
    removed_records: int = 0  # In file1 but not file2

    # Detailed differences
    record_differences: List[RecordDifference] = field(default_factory=list)
    comment_differences: List[tuple] = field(default_factory=list)

    # For raw diff
    raw_diff_lines: Optional[List[str]] = None

    @property
    def has_differences(self) -> bool:
        return (
            self.modified_records > 0
            or self.added_records > 0
            or self.removed_records > 0
        )


class SemanticComparator:
    """Semantic comparison of PBN files."""

    # Default tags to ignore (metadata, not game content)
    DEFAULT_IGNORE_TAGS: Set[str] = {"Site", "Event", "Date", "North", "South", "East", "West"}

    def __init__(
        self,
        compare_tags: Optional[List[str]] = None,
        ignore_tags: Optional[List[str]] = None,
    ):
        """
        Initialize comparator with optional tag filters.

        Args:
            compare_tags: If provided, only compare these tags
            ignore_tags: Tags to ignore in comparison (added to defaults)
        """
        self.compare_tags = set(compare_tags) if compare_tags else None
        self.ignore_tags = self.DEFAULT_IGNORE_TAGS.copy()
        if ignore_tags:
            self.ignore_tags.update(ignore_tags)

    def compare(self, file1: PBNFile, file2: PBNFile) -> DiffResult:
        """Compare two PBN files semantically."""

        # Build indexes by deal for matching
        index1 = file1.build_deal_index()
        index2 = file2.build_deal_index()

        all_deals = set(index1.keys()) | set(index2.keys())

        record_differences: List[RecordDifference] = []
        matched = 0
        modified = 0
        added = 0
        removed = 0

        for deal in sorted(
            all_deals, key=lambda d: self._deal_sort_key(d, index1, index2)
        ):
            rec1 = index1.get(deal)
            rec2 = index2.get(deal)

            if rec1 and rec2:
                # Both files have this deal - compare
                matched += 1
                tag_diffs = self._compare_records(rec1, rec2)
                if tag_diffs:
                    modified += 1
                    record_differences.append(
                        RecordDifference(
                            board_number=rec1.board_number,
                            deal=deal,
                            diff_type=DiffType.MODIFIED,
                            tag_differences=tag_diffs,
                        )
                    )
            elif rec1:
                # Only in file1 - removed
                removed += 1
                record_differences.append(
                    RecordDifference(
                        board_number=rec1.board_number,
                        deal=deal,
                        diff_type=DiffType.REMOVED,
                        tag_differences=[],
                    )
                )
            else:
                # Only in file2 - added
                added += 1
                record_differences.append(
                    RecordDifference(
                        board_number=rec2.board_number,
                        deal=deal,
                        diff_type=DiffType.ADDED,
                        tag_differences=[],
                    )
                )

        return DiffResult(
            file1_path=file1.path,
            file2_path=file2.path,
            mode="semantic",
            total_records_file1=len(file1.records),
            total_records_file2=len(file2.records),
            matched_records=matched,
            modified_records=modified,
            added_records=added,
            removed_records=removed,
            record_differences=record_differences,
            comment_differences=[],
        )

    def _compare_records(
        self, rec1: PBNRecord, rec2: PBNRecord
    ) -> List[TagDifference]:
        """Compare two records and return tag differences."""
        differences: List[TagDifference] = []

        # Get all tag names from both records
        all_tags = set(rec1.tags.keys()) | set(rec2.tags.keys())

        # Filter to only compare specified tags
        if self.compare_tags:
            all_tags = all_tags & self.compare_tags

        # Remove ignored tags
        all_tags = all_tags - self.ignore_tags

        for tag_name in sorted(all_tags):
            tag1 = rec1.tags.get(tag_name)
            tag2 = rec2.tags.get(tag_name)

            if tag1 and tag2:
                # Both have the tag
                if tag1.value != tag2.value:
                    differences.append(
                        TagDifference(
                            tag_name=tag_name,
                            diff_type=DiffType.MODIFIED,
                            value1=tag1.value,
                            value2=tag2.value,
                        )
                    )
            elif tag1:
                # Only in record1
                differences.append(
                    TagDifference(
                        tag_name=tag_name,
                        diff_type=DiffType.REMOVED,
                        value1=tag1.value,
                        value2=None,
                    )
                )
            else:
                # Only in record2
                differences.append(
                    TagDifference(
                        tag_name=tag_name,
                        diff_type=DiffType.ADDED,
                        value1=None,
                        value2=tag2.value,
                    )
                )

        return differences

    def _deal_sort_key(
        self, deal: str, index1: Dict[str, PBNRecord], index2: Dict[str, PBNRecord]
    ) -> int:
        """Sort key for deals - by board number."""
        rec = index1.get(deal) or index2.get(deal)
        return rec.board_number if rec else 0
