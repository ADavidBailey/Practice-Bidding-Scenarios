import os
import re
from collections import defaultdict
import sys


def get_hand_pattern(hand):
    """
    Calculates the hand pattern for a given bridge hand.
    Example: AQJ9.J6.AKJ63.T4 -> 4252 (Spades: 4, Hearts: 2, Diamonds: 5, Clubs: 2)
    """
    suits = hand.split(".")
    if len(suits) != 4:
        raise ValueError(f"Invalid hand format: {hand}")
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
        "W": ["West", "North", "East", "South"],
    }

    try:
        with open(input_file, "r") as infile:
            lines = infile.readlines()
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return

    for line in lines:
        line = line.strip()

        if line.startswith("[Deal "):
            deal_line = line[7:-2]
            first_hand = deal_line[0]
            hands = deal_line[2:].split(" ")
            hand_mapping = dict(zip(player_order_dict[first_hand], hands))

        elif line.startswith("[Auction"):
            first_seat = line[10]
            if first_seat not in player_order_dict:
                print(f"Error: Invalid first seat '{first_seat}' in line: {line}")
                continue
            auction = True

        elif auction:
            bids = line.split()
            player_order = ["N", "E", "S", "W"]
            start_index = player_order.index(first_seat)
            rotated_order = player_order[start_index:] + player_order[:start_index]

            for i, bid in enumerate(bids):
                if bid not in ("Pass", "="):  # Ignore "Pass" and "="
                    opening_bid = bid
                    opening_bidder = rotated_order[i % 4]
                    opening_hand = hand_mapping[player_order_dict[first_seat][i % 4]]
                    pattern = get_hand_pattern(opening_hand)

                    if opening_bid in pattern_counter[pattern]:
                        pattern_counter[pattern][opening_bid] += 1
                    else:
                        pattern_counter[pattern]["+"] += 1
                    break
            auction = False


def count_opening_patterns_in_folder(folder_path, filename_pattern):
    """
    Processes files in the specified folder based on the provided filename pattern 
    (supports wildcards and case-insensitive matching) and aggregates the pattern counts.
    """
    pattern_counter = defaultdict(
        lambda: {
            "1S": 0, "1H": 0, "1D": 0, "1C": 0, "1NT": 0,
            "2S": 0, "2H": 0, "2D": 0, "2C": 0, "2NT": 0,
            "3S": 0, "3H": 0, "3D": 0, "3C": 0, "3NT": 0,
            "+": 0,
        }
    )

    if "*" in filename_pattern:
        filename_pattern = filename_pattern.replace('*', '.*').lower()
    regex_pattern = re.compile(f"^{filename_pattern}$", re.IGNORECASE)
    print(regex_pattern)

    # Scan the folder and filter based on filenames (ignoring extensions)
    matching_files = [
        entry.path for entry in os.scandir(folder_path) 
        if entry.is_file() and regex_pattern.match(os.path.splitext(entry.name)[0].lower())
    ]

    if not matching_files:
        print(f"No files matched the pattern: {filename_pattern}")
        return pattern_counter, 0

    for file_path in matching_files:
        print(f"Processing file: {file_path}")
        count_opening_patterns_in_file(file_path, pattern_counter)

    return pattern_counter, len(matching_files)


def display_table(pattern_counts):
    """
    Displays the results in a table format with patterns as rows and opening bids as columns.
    """
    headers = ["Pattern", "1S", "1H", "1D", "1C", "1NT", "2S", "2H", "2D", "2C", "2NT",
               "3S", "3H", "3D", "3C", "3NT", "+", "Total"]
    column_widths = [10] + [5] * (len(headers) - 2) + [6]
    header_row = " ".join(f"{header:>{width}}" for header, width in zip(headers, column_widths))
    print(header_row)
    print("-" * (sum(column_widths) + len(column_widths) - 1))

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
    print("-" * (sum(column_widths) + len(column_widths) - 1))
    print(formatted_total_row)


def main():
    folder_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/"

    if len(sys.argv) > 1:
        filename_pattern = sys.argv[1]
        # Process .pbn files in the specified folder
        pattern_counts, file_count = count_opening_patterns_in_folder(folder_path, filename_pattern)
        if file_count > 0:
            print("\nOpening Bid Counts by Hand Pattern:\n")
            display_table(pattern_counts)
        else:
            print(f"No .pbn files matched the pattern '{filename_pattern}' in the folder '{folder_path}'.")
    else:
        print("Please provide a filename pattern as an argument.")

if __name__ == "__main__":
    main()
