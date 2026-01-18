"""
PBN file parser with data structures for comparison.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PBNTag:
    """A single PBN tag with name and value."""

    name: str
    value: str
    line_number: int

    def __eq__(self, other):
        if not isinstance(other, PBNTag):
            return False
        return self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash((self.name, self.value))


@dataclass
class AuctionData:
    """Parsed auction sequence."""

    dealer: str  # N/E/S/W
    bids: List[str] = field(default_factory=list)
    notes: Dict[int, str] = field(default_factory=dict)

    def normalized(self) -> str:
        """Return normalized auction string for comparison."""
        normalized_bids = [b.replace("Pass", "P") for b in self.bids]
        return "-".join(normalized_bids)


@dataclass
class PBNRecord:
    """A single deal/hand record from a PBN file."""

    board_number: int
    tags: Dict[str, PBNTag] = field(default_factory=dict)
    auction: Optional[AuctionData] = None
    raw_lines: List[str] = field(default_factory=list)
    start_line: int = 0
    end_line: int = 0

    @property
    def deal(self) -> Optional[str]:
        """The Deal tag value - uniquely identifies the hand."""
        tag = self.tags.get("Deal")
        return tag.value if tag else None

    @property
    def dealer(self) -> Optional[str]:
        """The Dealer tag value."""
        tag = self.tags.get("Dealer")
        return tag.value if tag else None

    @property
    def vulnerable(self) -> Optional[str]:
        """The Vulnerable tag value."""
        tag = self.tags.get("Vulnerable")
        return tag.value if tag else None

    def get_tag_value(self, name: str) -> Optional[str]:
        """Get value of a specific tag."""
        tag = self.tags.get(name)
        return tag.value if tag else None

    def semantic_key(self) -> str:
        """Key for matching records across files (by Deal)."""
        return self.deal or f"board_{self.board_number}"


@dataclass
class PBNFile:
    """A complete parsed PBN file."""

    path: str
    comments: List[Tuple[int, str]] = field(default_factory=list)
    records: List[PBNRecord] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def get_record_by_board(self, board_num: int) -> Optional[PBNRecord]:
        """Find record by board number."""
        for rec in self.records:
            if rec.board_number == board_num:
                return rec
        return None

    def get_record_by_deal(self, deal: str) -> Optional[PBNRecord]:
        """Find record by deal string."""
        for rec in self.records:
            if rec.deal == deal:
                return rec
        return None

    def build_deal_index(self) -> Dict[str, PBNRecord]:
        """Build index by deal for fast lookup."""
        return {rec.deal: rec for rec in self.records if rec.deal}


class PBNParser:
    """Parser for PBN files."""

    TAG_PATTERN = re.compile(r'^\[(\w+)\s+"(.*)"\]$')
    AUCTION_TAG_PATTERN = re.compile(r'^\[Auction\s+"([NESW])"\]$')
    NOTE_PATTERN = re.compile(r'^\[Note\s+"(\d+):(.*)"\]$')

    def parse_file(self, path: str) -> PBNFile:
        """Parse a PBN file into structured data."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        comments: List[Tuple[int, str]] = []
        records: List[PBNRecord] = []
        metadata: Dict[str, str] = {}
        current_record_lines: List[Tuple[int, str]] = []
        current_record_start = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.rstrip("\n\r")

            # Handle comments (% at start of line)
            if stripped.startswith("%"):
                if not current_record_lines:
                    # File-level comment
                    comment_text = stripped[1:].strip()
                    comments.append((line_num, comment_text))
                    self._extract_metadata(comment_text, metadata)
                continue

            # Empty line - end of record
            if not stripped.strip():
                if current_record_lines:
                    record = self._parse_record(
                        current_record_lines, current_record_start, line_num - 1
                    )
                    if record:
                        records.append(record)
                    current_record_lines = []
                continue

            # Start of new record or continuation
            if not current_record_lines:
                current_record_start = line_num
            current_record_lines.append((line_num, stripped))

        # Handle final record (if no trailing blank line)
        if current_record_lines:
            record = self._parse_record(
                current_record_lines, current_record_start, len(lines)
            )
            if record:
                records.append(record)

        return PBNFile(
            path=path, comments=comments, records=records, metadata=metadata
        )

    def _extract_metadata(self, comment: str, metadata: Dict[str, str]) -> None:
        """Extract metadata from comment lines."""
        if ":" in comment:
            key, _, value = comment.partition(":")
            key = key.strip()
            value = value.strip()
            if key and value:
                metadata[key] = value

    def _parse_record(
        self, lines: List[Tuple[int, str]], start: int, end: int
    ) -> Optional[PBNRecord]:
        """Parse a single record from lines."""
        tags: Dict[str, PBNTag] = {}
        raw_lines: List[str] = []
        board_number = 0

        in_auction = False
        auction_bids: List[str] = []
        auction_dealer = ""
        notes: Dict[int, str] = {}

        for line_num, line in lines:
            raw_lines.append(line)

            # Check for tag
            tag_match = self.TAG_PATTERN.match(line)
            if tag_match:
                name, value = tag_match.groups()
                tags[name] = PBNTag(name=name, value=value, line_number=line_num)

                if name == "Board":
                    try:
                        board_number = int(value)
                    except ValueError:
                        pass

                # Check for Auction start
                auction_match = self.AUCTION_TAG_PATTERN.match(line)
                if auction_match:
                    auction_dealer = auction_match.group(1)
                    in_auction = True
                    auction_bids = []
                    continue

                # Check for Note
                note_match = self.NOTE_PATTERN.match(line)
                if note_match:
                    note_num, note_text = note_match.groups()
                    notes[int(note_num)] = note_text
                    continue

                # Other tag ends auction section
                if in_auction:
                    in_auction = False
                continue

            # Non-tag line in auction section
            if in_auction and line.strip():
                # Split by whitespace
                bids = line.split()
                auction_bids.extend(bids)

        # Build auction data if we found an auction
        auction_data = None
        if auction_dealer and auction_bids:
            auction_data = AuctionData(
                dealer=auction_dealer, bids=auction_bids, notes=notes
            )

        if board_number == 0 and "Board" not in tags:
            return None

        return PBNRecord(
            board_number=board_number,
            tags=tags,
            auction=auction_data,
            raw_lines=raw_lines,
            start_line=start,
            end_line=end,
        )
