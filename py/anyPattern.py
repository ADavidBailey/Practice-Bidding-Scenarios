import os
import re
from collections import defaultdict

def get_hand_pattern(hand):
    """
    Calculates the hand pattern for a given bridge hand.
    Example: AQJ9.J6.AKJ63.T4 -> 4252 (Spades: 4, Hearts: 2, Diamonds: 5, Clubs: 2)
    """
    suits = hand.split(".")
    return "".join(str(len(suit)) for suit in suits)

def count_opening_patterns_in_file(input_file, pattern_counter):
    """
    Reads a file of hands, determines the pattern of each hand,
    and counts the occurrences of each opening bid for each hand pattern.
    Updates the provided pattern_counter.
    """
    auction = False
    hand_mapping = {}
    player_order_dict = {
        "N": ["North", "East", "South", "West"],
        "E": ["East", "South", "West", "North"],
        "S": ["South", "West", "North", "East"],
        "W": ["West", "North", "East", "South"]
    }

    with open(input_file, "r") as infile:
        lines = infile.readlines()

    for line in lines:
        line = line.strip()

        # Parse the deal line
        if line.startswith("[Deal "):
            deal_line = line[7:-2]
            first_hand = deal_line[0]
            hands = deal_line[2:].split(" ")
            hand_mapping = dict(zip(player_order_dict[first_hand], hands))

        # Parse the auction line
        elif line.startswith("[Auction"):
            first_seat = line[10]
            auction = True

        # Process the auction sequence
        elif auction:
            bids = line.split()
            player_order = ["N", "E", "S", "W"]
            start_index = player_order.index(first_seat)
            rotated_order = player_order[start_index:] + player_order[:start_index]

            for i, bid in enumerate(bids):
                if bid not in ("Pass", "="):  # Ignore "Pass" and annotations like "=1="
                    # Normalize shorthand 'N' to 'NT' in bids
                    opening_bid = bid
                    opening_hand = hand_mapping[player_order_dict[first_seat][i % 4]]
                    pattern = get_hand_pattern(opening_hand)

                    # Group bids of 4, 5, 6, 7 into the "+" column
                    if opening_bid.startswith(("4", "5", "6", "7")):
                        pattern_counter[pattern]["+"] += 1
                    else:
                        pattern_counter[pattern][opening_bid] += 1
                    break

                auction = False

def count_opening_patterns_in_folder(folder_path, filename_pattern):
    """
    Processes files in the specified folder based on the provided filename pattern 
    (supports wildcards and case-insensitive matching) and aggregates the pattern counts.
    """
    pattern_counter = defaultdict(lambda: {
        "1S": 0, "1H": 0, "1D": 0, "1C": 0, "1NT": 0,
        "2S": 0, "2H": 0, "2D": 0, "2C": 0, "2NT": 0,
        "3S": 0, "3H": 0, "3D": 0, "3C": 0, "3NT": 0,
        "+": 0
    })

    if "*" in filename_pattern:
        filename_pattern = filename_pattern.replace('*', '.*').lower()
    regex_pattern = re.compile(rf"^{filename_pattern}\.pbn$", re.IGNORECASE)

    matching_files = [entry.path for entry in os.scandir(folder_path) if entry.is_file() and entry.name.lower().endswith('.pbn')]
    matching_files = [file for file in matching_files if regex_pattern.match(os.path.basename(file).lower())]

    if not matching_files:
        print(f"No files matched the pattern: {filename_pattern}")
        return pattern_counter

    for file_path in matching_files:
        print(f"Processing file: {file_path}")
        count_opening_patterns_in_file(file_path, pattern_counter)
    
    return pattern_counter

def display_table(pattern_counts):
    """
    Displays the results in a table format with patterns as rows and opening bids as columns.
    """
    headers = ["Pattern", "1S", "1H", "1D", "1C", "1NT", "2S", "2H", "2D", "2C", "2NT", 
               "3S", "3H", "3D", "3C", "3NT", "+", "Total"]
    column_widths = [10] + [5] * (len(headers) - 2) + [6]
    header_row = " ".join(f"{header:>{width}}" for header, width in zip(headers, column_widths))
    print(header_row)
    print("-" * sum(column_widths))
    column_totals = {bid: 0 for bid in headers[1:-1]}
    
    for pattern, counts in sorted(pattern_counts.items()):
        row_total = sum(counts.values())
        row = [pattern] + [counts[bid] for bid in headers[1:-1]] + [row_total]
        formatted_row = " ".join(f"{value:>{width}}" for value, width in zip(row, column_widths))
        print(formatted_row)
        for bid in column_totals:
            column_totals[bid] += counts[bid]
    
    total_row = ["Total"] + [column_totals[bid] for bid in headers[1:-1]] + [sum(column_totals.values())]
    formatted_total_row = " ".join(f"{value:>{width}}" for value, width in zip(total_row, column_widths))
    print("-" * sum(column_widths))
    print(formatted_total_row)

# Example usage
import sys

def main():
    folder_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/"

    # Accept filename pattern as a command-line argument, or prompt if not provided
    if len(sys.argv) > 1:
        filename_pattern = sys.argv[1]
    else:
        filename_pattern = input("Enter filename pattern (e.g., 'Jacoby*' or 'start*end'): ").strip()

    pattern_counts = count_opening_patterns_in_folder(folder_path, filename_pattern)
    print("Opening Bid Counts by Hand Pattern:")
    display_table(pattern_counts)

if __name__ == "__main__":
    main()
