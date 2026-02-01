"""
Quiz operation: Generate quiz sets from filtered BBA files.

Analyzes auction frequencies and creates varied quiz sets for each
bidding decision point where multiple bids occur with >5% frequency.

REQUIREMENTS:
=============

1. INPUT/OUTPUT:
   - Read the filtered-in PBN file (bba-filtered/{scenario}.pbn)
   - Output quiz PBN and PDF to /quiz folder

2. PARAMETERS:
   - num_per_quiz: Number of hands per quiz set (default: 6)
   - min_frequency: Minimum bid frequency to include (default: 5%)

3. AUCTION ANALYSIS:
   - Analyze auction frequencies at each decision level
   - Cycle through opener and responder decision points
   - Skip levels where only one bid occurs (no decision to make)
   - Skip bids with <5% frequency (too rare to quiz)

4. QUIZ GENERATION ALGORITHM:
   a) Start with opening bid level
      - Count frequency of each opening bid
      - If only one opening (e.g., all 1NT), skip this level
      - Otherwise, create a quiz with varied opening hands

   b) Move to responder's first bid
      - After common opening, count response frequencies
      - Example: After 1NT, responses might be Pass (6%) or 2C (94%)
      - Since both are >5%, create quiz: "Partner opens 1NT. What do you bid?"

   c) Return to opener's rebid
      - After 1NT-Pass-2C, count opener's rebids (2D, 2H, 2S)
      - Quiz: "You open 1NT and partner responds 2C, what do you bid?"

   d) Continue alternating until auctions conclude
      - Skip opponent bids (we only quiz our side's decisions)
      - Skip terminal positions (all remaining bids are Pass)

5. HAND SELECTION FOR EACH QUIZ:
   - Try for equal distribution of correct answers
   - Maximize variety in the remaining auction after the quizzed bid
   - Select from different continuations to show range of possibilities

6. QUIZ PROMPTS:
   - For responder: "Partner opens {bid}. What do you bid?"
   - For opener rebid: "You open {bid}, partner responds {bid}. What do you bid?"
   - Include full auction context as it builds

7. OUTPUT FORMAT (Console for now):
   - Show auction prefix and bid distribution
   - Display 6 hands with suit symbols
   - Show correct answer and full auction for each hand
"""
import os
import re
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FOLDERS, MAC_TOOLS, PROJECT_ROOT


class Hand:
    """Represents a bridge hand with cards and auction."""
    def __init__(self, board_num: int, dealer: str, hands: Dict[str, str], auction: List[str]):
        self.board_num = board_num
        self.dealer = dealer  # N, E, S, W
        self.hands = hands    # {'N': 'xxx.xxx.xxx.xxx', 'S': '...', etc}
        self.auction = auction  # ['1N', 'Pass', '2C', 'Pass', '2D', ...]

    def get_auction_at_level(self, level: int) -> List[str]:
        """Get auction up to and including the specified bid level (0-indexed)."""
        return self.auction[:level + 1]

    def get_bid_at_level(self, level: int) -> Optional[str]:
        """Get the bid at the specified level (0-indexed)."""
        if level < len(self.auction):
            return self.auction[level]
        return None

    def __repr__(self):
        return f"Hand({self.board_num}, {self.auction})"


def parse_pbn_file(pbn_path: str) -> List[Hand]:
    """Parse a PBN file and extract hands with auctions."""
    hands = []

    with open(pbn_path, 'r') as f:
        content = f.read()

    # Split into boards
    boards = re.split(r'\[Event ', content)[1:]

    for board_text in boards:
        try:
            # Extract board number
            board_match = re.search(r'\[Board "(\d+)"\]', board_text)
            board_num = int(board_match.group(1)) if board_match else 0

            # Extract dealer
            dealer_match = re.search(r'\[Dealer "([NESW])"\]', board_text)
            dealer = dealer_match.group(1) if dealer_match else 'S'

            # Extract deal
            deal_match = re.search(r'\[Deal "([^"]+)"\]', board_text)
            if not deal_match:
                continue
            deal_str = deal_match.group(1)

            # Parse deal string like "S:xxx.xxx.xxx.xxx xxx.xxx.xxx.xxx ..."
            # Format is "first_seat:hand hand hand hand" going clockwise
            deal_parts = deal_str.split(':')
            first_seat = deal_parts[0]
            hand_strs = deal_parts[1].split()

            # Map seats in clockwise order from first_seat
            seat_order = ['N', 'E', 'S', 'W']
            start_idx = seat_order.index(first_seat)
            hands_dict = {}
            for i, hand_str in enumerate(hand_strs):
                seat = seat_order[(start_idx + i) % 4]
                hands_dict[seat] = hand_str

            # Extract auction
            auction_match = re.search(r'\[Auction "[NESW]"\]\n(.*?)(?=\n\[|\Z)', board_text, re.DOTALL)
            if not auction_match:
                continue

            auction_text = auction_match.group(1)
            # Clean up auction - remove comments and alerts
            auction_text = re.sub(r'\{[^}]*\}', '', auction_text)  # Remove {comments}
            auction_text = re.sub(r'=[^=]*=', '', auction_text)    # Remove =alerts=

            # Parse bids
            auction = []
            for bid in auction_text.split():
                bid = bid.strip()
                if bid and bid not in ['', '*']:
                    # Normalize bid names
                    bid = bid.replace('NT', 'N')
                    auction.append(bid)

            if auction:
                hands.append(Hand(board_num, dealer, hands_dict, auction))

        except Exception as e:
            # Skip malformed boards
            continue

    return hands


def get_bidder_at_level(dealer: str, level: int) -> str:
    """
    Determine who is bidding at a given level.
    Level 0 = dealer, level 1 = LHO, level 2 = partner, level 3 = RHO, etc.
    Returns 'opener', 'responder', 'lho', or 'rho'.
    """
    # For simplicity, assume dealer is always the opener (South in our scenarios)
    # Level 0, 4, 8, ... = opener
    # Level 1, 5, 9, ... = LHO (opponent)
    # Level 2, 6, 10, ... = responder (partner)
    # Level 3, 7, 11, ... = RHO (opponent)

    position = level % 4
    if position == 0:
        return 'opener'
    elif position == 1:
        return 'lho'
    elif position == 2:
        return 'responder'
    else:
        return 'rho'


def analyze_auction_tree(hands: List[Hand], min_frequency: float = 0.05) -> Dict:
    """
    Build an auction tree with frequency analysis at each level.

    Returns a nested structure showing bid frequencies at each decision point.
    """
    # Build frequency counts at each level, grouped by prefix
    level_data = defaultdict(lambda: defaultdict(list))

    for hand in hands:
        for level in range(len(hand.auction)):
            prefix = tuple(hand.auction[:level])
            bid = hand.auction[level]
            level_data[prefix][bid].append(hand)

    return level_data


def format_hand_for_display(hand_str: str) -> str:
    """Format a hand string for display with suit symbols."""
    suits = hand_str.split('.')
    symbols = ['♠', '♥', '♦', '♣']
    parts = []
    for symbol, cards in zip(symbols, suits):
        if cards:
            parts.append(f"{symbol}{cards}")
        else:
            parts.append(f"{symbol}-")
    return ' '.join(parts)


def format_auction_prefix(auction: List[str]) -> str:
    """Format an auction prefix for display."""
    if not auction:
        return ""

    # Convert back to readable format
    formatted = []
    for bid in auction:
        bid = bid.replace('N', 'NT')
        formatted.append(bid)

    return ' - '.join(formatted)


def generate_quiz_prompt(bidder: str, auction_prefix: List[str], dealer: str = 'S') -> str:
    """Generate the quiz prompt for a given bidding situation."""

    if not auction_prefix:
        if bidder == 'opener':
            return "What do you open with each of these hands?"
        else:
            return "Partner opens. What do you respond with each of these hands?"

    # Build the narrative
    formatted_auction = []
    for i, bid in enumerate(auction_prefix):
        bid_display = bid.replace('N', 'NT')
        who = get_bidder_at_level(dealer, i)
        formatted_auction.append((who, bid_display))

    if bidder == 'opener':
        # Opener's rebid situation
        parts = []
        for who, bid in formatted_auction:
            if who == 'opener':
                parts.append(f"You open {bid}")
            elif who == 'responder':
                parts.append(f"partner responds {bid}")
            elif who in ('lho', 'rho'):
                if bid != 'Pass':
                    parts.append(f"opponent bids {bid}")

        prompt = ', '.join(parts) + ". What do you bid with each of these hands?"

    else:  # responder
        parts = []
        for who, bid in formatted_auction:
            if who == 'opener':
                parts.append(f"Partner opens {bid}")
            elif who == 'responder':
                parts.append(f"you respond {bid}")
            elif who in ('lho', 'rho'):
                if bid != 'Pass':
                    parts.append(f"opponent bids {bid}")

        prompt = ', '.join(parts) + ". What do you bid with each of these hands?"

    return prompt


def select_quiz_hands(hands_by_bid: Dict[str, List[Hand]],
                      num_hands: int = 6,
                      bidder: str = 'opener') -> List[Tuple[Hand, str]]:
    """
    Select hands for a quiz with good variety.

    Try to get equal distribution of bids, with variety in the remaining auction.
    Returns list of (Hand, correct_bid) tuples.
    """
    selected = []
    bids = list(hands_by_bid.keys())

    if not bids:
        return []

    # Calculate how many of each bid to include
    per_bid = max(1, num_hands // len(bids))
    remainder = num_hands - (per_bid * len(bids))

    for bid in bids:
        available = hands_by_bid[bid]
        if not available:
            continue

        # How many to take of this bid
        count = per_bid
        if remainder > 0:
            count += 1
            remainder -= 1

        # Sort by variety in remaining auction (prefer different continuations)
        # Group by next few bids to get variety
        by_continuation = defaultdict(list)
        for hand in available:
            # Get next 2-3 bids as continuation key
            bid_idx = len([b for b in hand.auction if b == bid])  # Rough position
            continuation = tuple(hand.auction[bid_idx:bid_idx+3]) if bid_idx < len(hand.auction) else ()
            by_continuation[continuation].append(hand)

        # Select from different continuations
        continuations = list(by_continuation.keys())
        added = 0
        cont_idx = 0
        while added < count and added < len(available):
            cont = continuations[cont_idx % len(continuations)]
            if by_continuation[cont]:
                hand = by_continuation[cont].pop(0)
                selected.append((hand, bid))
                added += 1
            cont_idx += 1
            # Safety check to avoid infinite loop
            if cont_idx > count * 2:
                break

    return selected[:num_hands]


def generate_quizzes(hands: List[Hand],
                     num_per_quiz: int = 6,
                     min_frequency: float = 0.05,
                     verbose: bool = True) -> List[Dict]:
    """
    Generate quiz sets from the hands.

    Returns a list of quiz dictionaries, each containing:
    - 'level': The auction level being quizzed
    - 'prefix': The auction prefix (previous bids)
    - 'bidder': 'opener' or 'responder'
    - 'prompt': The quiz prompt text
    - 'hands': List of (Hand, correct_bid) tuples
    - 'bid_distribution': Dict of bid -> count
    """
    quizzes = []
    level_data = analyze_auction_tree(hands)

    # Process each decision point
    processed_prefixes = set()

    for prefix, bids_dict in sorted(level_data.items(), key=lambda x: len(x[0])):
        if prefix in processed_prefixes:
            continue
        processed_prefixes.add(prefix)

        level = len(prefix)
        bidder = get_bidder_at_level('S', level)  # Assume South is dealer

        # Skip opponent bids - we only quiz our side
        if bidder in ('lho', 'rho'):
            continue

        # Count total hands at this decision point
        total_hands = sum(len(h) for h in bids_dict.values())
        if total_hands == 0:
            continue

        # Filter bids by frequency
        significant_bids = {}
        for bid, bid_hands in bids_dict.items():
            frequency = len(bid_hands) / total_hands
            if frequency >= min_frequency:
                significant_bids[bid] = bid_hands

        # Skip if only one significant bid (no decision to make)
        if len(significant_bids) <= 1:
            if verbose:
                prefix_str = format_auction_prefix(list(prefix))
                if significant_bids:
                    bid = list(significant_bids.keys())[0]
                    print(f"  Level {level} after [{prefix_str}]: Only one bid ({bid}) - skipping")
            continue

        # Skip if all remaining auctions end (all Pass)
        non_pass_bids = {b: h for b, h in significant_bids.items() if b != 'Pass'}
        if not non_pass_bids and 'Pass' in significant_bids:
            # Only passes remain - these are terminal positions
            continue

        # Generate the quiz
        prompt = generate_quiz_prompt(bidder, list(prefix))
        quiz_hands = select_quiz_hands(significant_bids, num_per_quiz, bidder)

        if len(quiz_hands) < 2:
            continue

        bid_distribution = {bid: len(hands) for bid, hands in significant_bids.items()}

        quiz = {
            'level': level,
            'prefix': list(prefix),
            'bidder': bidder,
            'prompt': prompt,
            'hands': quiz_hands,
            'bid_distribution': bid_distribution,
            'total_hands': total_hands
        }
        quizzes.append(quiz)

    return quizzes


def display_quiz(quiz: Dict, quiz_num: int):
    """Display a quiz to console."""
    print(f"\n{'='*70}")
    print(f"QUIZ {quiz_num}: {quiz['bidder'].upper()}'S DECISION")
    print(f"{'='*70}")

    prefix_str = format_auction_prefix(quiz['prefix'])
    if prefix_str:
        print(f"Auction so far: {prefix_str}")

    print(f"\n{quiz['prompt']}\n")

    # Show bid distribution
    print("Bid frequencies at this point:")
    for bid, count in sorted(quiz['bid_distribution'].items(),
                             key=lambda x: -x[1]):
        pct = count / quiz['total_hands'] * 100
        bid_display = bid.replace('N', 'NT')
        print(f"  {bid_display}: {count} ({pct:.1f}%)")

    print(f"\n{'─'*70}")
    print("Quiz Hands:")
    print(f"{'─'*70}\n")

    # Determine which seat to show based on bidder
    show_seat = 'S' if quiz['bidder'] == 'opener' else 'N'

    for i, (hand, correct_bid) in enumerate(quiz['hands'], 1):
        hand_str = hand.hands.get(show_seat, '')
        formatted = format_hand_for_display(hand_str)
        correct_display = correct_bid.replace('N', 'NT')

        print(f"  {i}. {formatted}")
        print(f"     Answer: {correct_display}")
        print(f"     Full auction: {' - '.join(b.replace('N', 'NT') for b in hand.auction)}")
        print()


def convert_suits_for_pbn(text: str) -> str:
    """Convert suit bids in text to PBN suit symbols (\\S, \\H, \\D, \\C)."""
    # Convert bid patterns like 1NT, 2H, 3S, etc.
    # Also handle standalone suit mentions
    result = text

    # Replace bids with suit - match patterns like "1H", "2S", "3D", "4C"
    # and also "opens 1H", "responds 2C", etc.
    result = re.sub(r'\b(\d)S\b', r'\1\\S', result)
    result = re.sub(r'\b(\d)H\b', r'\1\\H', result)
    result = re.sub(r'\b(\d)D\b', r'\1\\D', result)
    result = re.sub(r'\b(\d)C\b', r'\1\\C', result)

    return result


def has_interference(prefix: List[str]) -> bool:
    """Check if the auction prefix contains any non-pass opponent bids."""
    for i, bid in enumerate(prefix):
        bidder = get_bidder_at_level('S', i)
        if bidder in ('lho', 'rho') and bid != 'Pass':
            return True
    return False


def generate_pbn_header(scenario: str, use_two_col: bool = True) -> str:
    """Generate PBN file header with formatting settings for quiz layout."""
    two_col = " TwoColAuctions" if use_two_col else ""
    return f"""% PBN 2.1
% EXPORT
%Content-type: text/x-pbn; charset=UTF-8
%BCOptions Center GutterH GutterV Justify PageHeader STBorder STShade{two_col}
%BidAndCardSpacing Thin
%BoardsPerPage fit,2
%CardTableColors #008000,#ffffff,#aaaaaa
%EventSpacing 12
%Font:CardTable "Arial",11,400,0
%Font:Commentary "Arial",12,400,0
%Font:Diagram "Arial",12,400,0
%Font:Event "Arial",16,700,0
%Font:FixedPitch "Courier New",10,400,0
%Font:HandRecord "Arial",11,400,0
%GutterSize 250,250
%HRTitleEvent "{scenario} - Bidding Quiz"
%Margins 1000,1000,1000,750
%PageFooter:0,0 "%D"
%PageFooter:0,2 "%n"
%PaperSize 1,2159,2794,2
%ParaIndent 0
%PipColors #000000,#ff0000,#ff0000,#000000
%ShowBoardLabels 1
%ShowCardTable 2
%Translate "Board %" "%)"
"""


def format_auction_for_pbn(prefix: List[str], include_plus: bool = True) -> str:
    """Format auction prefix for PBN [Auction] tag."""
    if not prefix:
        return "+"

    # Convert bids to PBN format
    formatted = []
    for bid in prefix:
        bid = bid.replace('N', 'NT')
        formatted.append(bid)

    # Add Pass placeholders for skipped positions and the + marker
    result = ' '.join(formatted)
    if include_plus:
        result += '\n+'

    return result


def generate_quiz_pbn(quizzes: List[Dict], scenario: str) -> str:
    """Generate complete PBN file content for all quizzes."""
    # Check if any quizzes have interference - if not, use two-column auctions
    any_interference = any(has_interference(q['prefix']) for q in quizzes)
    lines = [generate_pbn_header(scenario, use_two_col=not any_interference)]

    for quiz_num, quiz in enumerate(quizzes, 1):
        bidder = quiz['bidder']
        prefix = quiz['prefix']
        prompt = quiz['prompt']

        # Convert suit symbols in prompt
        prompt_pbn = convert_suits_for_pbn(prompt)

        # Determine which seat shows the hand
        show_seat = 'S' if bidder == 'opener' else 'N'
        hidden = 'NEW' if show_seat == 'S' else 'ESW'

        # Determine if we need to show auction (skip if prompt describes it fully)
        # Show auction only if there's interference or complex bidding
        show_auction = prefix and has_interference(prefix)

        # Quiz header board with instructions
        lines.append(f'[Event "{scenario} Quiz {quiz_num}"]')
        lines.append('[Site ""]')
        lines.append('[Date ""]')
        lines.append('{<b>' + prompt_pbn + '</b>}')
        lines.append(f'[Board "{quiz_num}"]')
        lines.append('[West ""]')
        lines.append('[North ""]')
        lines.append('[East ""]')
        lines.append('[South ""]')
        lines.append('[Dealer "S"]')
        lines.append('[Vulnerable "None"]')
        lines.append('[Deal ""]')
        lines.append('[Scoring ""]')
        lines.append('[Declarer ""]')
        lines.append('[Contract ""]')
        lines.append('[Result ""]')
        lines.append('[BCFlags "600023"]')
        lines.append('[Hidden "NESW"]')

        # Add auction context only if there's interference
        if show_auction:
            lines.append('[Auction "S"]')
            lines.append(format_auction_for_pbn(prefix) + ' $2')

        lines.append('')

        # Individual hand boards
        for hand_num, (hand, correct_bid) in enumerate(quiz['hands'], 1):
            board_id = f"{quiz_num}-{hand_num}"

            # Get the hand string for the seat we're showing
            hand_str = hand.hands.get(show_seat, '...')

            # Format deal string - show only the relevant hand
            if show_seat == 'S':
                deal_str = f'S:{hand_str} ... ... ...'
            else:  # N
                deal_str = f'N:{hand_str} ... ... ...'

            # Format the answer with suit symbol
            answer_bid = correct_bid.replace('N', 'NT')
            answer_pbn = convert_suits_for_pbn(answer_bid)

            lines.append('[Event ""]')
            lines.append('[Site ""]')
            lines.append('[Date ""]')
            lines.append(f'[Board "{board_id}"]')
            lines.append('[West ""]')
            lines.append('[North ""]')
            lines.append('[East ""]')
            lines.append('[South ""]')
            lines.append('[Dealer "S"]')
            lines.append('[Vulnerable "None"]')
            lines.append(f'[Deal "{deal_str}"]')
            lines.append('[Scoring ""]')
            lines.append('[Declarer ""]')
            lines.append('[Contract ""]')
            lines.append('[Result ""]')
            lines.append('{<i>' + answer_pbn + '</i>}')
            lines.append('[BCFlags "60001b"]')
            lines.append(f'[Hidden "{hidden}"]')

            # Add auction context only if there's interference
            if show_auction:
                lines.append('[Auction "S"]')
                lines.append(format_auction_for_pbn(prefix) + ' $2')

            lines.append('')

        # Add spacer board between quiz and answers
        lines.append('[Event ""]')
        lines.append('[Site ""]')
        lines.append('[Date ""]')
        lines.append('[Board "spacer"]')
        lines.append('[West ""]')
        lines.append('[North ""]')
        lines.append('[East ""]')
        lines.append('[South ""]')
        lines.append('[Dealer "N"]')
        lines.append('[Vulnerable "None"]')
        lines.append('[Deal ""]')
        lines.append('[Scoring ""]')
        lines.append('[Declarer ""]')
        lines.append('[Contract ""]')
        lines.append('[Result ""]')
        lines.append('{')
        for _ in range(12):
            lines.append('')
        lines.append(' }')
        lines.append('[BCFlags "17"]')
        lines.append('')

        # ========== ANSWER SHEET ==========
        # Answer header
        lines.append('[Event ""]')
        lines.append('[Site ""]')
        lines.append('[Date ""]')
        lines.append('{<b><i>Quiz ' + str(quiz_num) + ' Answers</i></b>}')
        lines.append(f'[Board "{quiz_num}"]')
        lines.append('[West ""]')
        lines.append('[North ""]')
        lines.append('[East ""]')
        lines.append('[South ""]')
        lines.append('[Dealer "S"]')
        lines.append('[Vulnerable "None"]')
        lines.append('[Deal ""]')
        lines.append('[Scoring ""]')
        lines.append('[Declarer ""]')
        lines.append('[Contract ""]')
        lines.append('[Result ""]')
        lines.append('[BCFlags "600023"]')
        lines.append('[Hidden "NESW"]')
        lines.append('')

        # Individual answer entries
        for hand_num, (hand, correct_bid) in enumerate(quiz['hands'], 1):
            board_id = f"{quiz_num}-{hand_num}"
            answer_bid = correct_bid.replace('N', 'NT')
            answer_pbn = convert_suits_for_pbn(answer_bid)

            # Format the full auction for the answer
            full_auction = ' - '.join(b.replace('N', 'NT') for b in hand.auction)
            full_auction_pbn = convert_suits_for_pbn(full_auction)

            lines.append('[Event ""]')
            lines.append('[Site ""]')
            lines.append('[Date ""]')
            lines.append(f'[Board "{board_id}"]')
            lines.append('[West ""]')
            lines.append('[North ""]')
            lines.append('[East ""]')
            lines.append('[South ""]')
            lines.append('[Dealer "N"]')
            lines.append('[Vulnerable "None"]')
            lines.append('[Deal ""]')
            lines.append('[Scoring ""]')
            lines.append('[Declarer ""]')
            lines.append('[Contract ""]')
            lines.append('[Result ""]')
            lines.append('{<b>' + board_id + ')</b> <i>' + answer_pbn + '</i>}')
            lines.append('[BCFlags "17"]')
            lines.append('')

        # Spacer after answers
        lines.append('[Event ""]')
        lines.append('[Site ""]')
        lines.append('[Date ""]')
        lines.append('[Board "spacer"]')
        lines.append('[West ""]')
        lines.append('[North ""]')
        lines.append('[East ""]')
        lines.append('[South ""]')
        lines.append('[Dealer "N"]')
        lines.append('[Vulnerable "None"]')
        lines.append('[Deal ""]')
        lines.append('[Scoring ""]')
        lines.append('[Declarer ""]')
        lines.append('[Contract ""]')
        lines.append('[Result ""]')
        lines.append('{')
        for _ in range(18):
            lines.append('')
        lines.append(' }')
        lines.append('[BCFlags "17"]')
        lines.append('')

    return '\n'.join(lines)


def run_quiz(scenario: str, num_per_quiz: int = 6, verbose: bool = True) -> bool:
    """
    Generate quizzes for a scenario.

    Args:
        scenario: Scenario name (e.g., "Stayman")
        num_per_quiz: Number of hands per quiz (default 6)
        verbose: Whether to print progress

    Returns:
        True if successful, False otherwise
    """
    if verbose:
        print(f"--------- Quiz generation for {scenario}")

    # Read filtered PBN file
    filtered_path = os.path.join(FOLDERS["bba_filtered"], f"{scenario}.pbn")
    if not os.path.exists(filtered_path):
        print(f"Error: Filtered file not found: {filtered_path}")
        return False

    if verbose:
        print(f"  Reading: {filtered_path}")

    # Parse hands
    hands = parse_pbn_file(filtered_path)
    if verbose:
        print(f"  Parsed {len(hands)} hands")

    if not hands:
        print("  No hands found in file")
        return False

    # Generate quizzes
    print(f"\nAnalyzing auction decision points...")
    quizzes = generate_quizzes(hands, num_per_quiz, verbose=verbose)

    if not quizzes:
        print("  No quiz-worthy decision points found")
        return True

    print(f"\nGenerated {len(quizzes)} quiz sets")

    # Display quizzes to console
    for i, quiz in enumerate(quizzes, 1):
        display_quiz(quiz, i)

    # Create quiz output folder
    quiz_folder = os.path.join(PROJECT_ROOT, "quiz")
    os.makedirs(quiz_folder, exist_ok=True)

    # Generate PBN file
    pbn_content = generate_quiz_pbn(quizzes, scenario)
    pbn_path = os.path.join(quiz_folder, f"{scenario}.pbn")

    with open(pbn_path, 'w', encoding='utf-8') as f:
        f.write(pbn_content)

    if verbose:
        print(f"\n  Created: {pbn_path}")

    # Generate PDF using bridge-wrangler
    bridge_wrangler = MAC_TOOLS.get("bridge_wrangler")
    if bridge_wrangler:
        pdf_path = os.path.join(quiz_folder, f"{scenario}.pdf")
        pdf_cmd = [
            bridge_wrangler, "to-pdf",
            "-i", pbn_path,
            "-o", pdf_path
        ]

        try:
            result = subprocess.run(pdf_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  Warning: PDF generation failed")
                if result.stderr:
                    print(f"    {result.stderr}")
            elif verbose:
                print(f"  Created: {pdf_path}")
        except Exception as e:
            print(f"  Warning: PDF generation failed: {e}")

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
    else:
        scenario = "Stayman"

    num_per_quiz = 6
    if len(sys.argv) > 2:
        num_per_quiz = int(sys.argv[2])

    print(f"Quiz Generation Test")
    print(f"Scenario: {scenario}")
    print(f"Hands per quiz: {num_per_quiz}")
    print()

    success = run_quiz(scenario, num_per_quiz)
    print(f"\nResult: {'Success' if success else 'Failed'}")
