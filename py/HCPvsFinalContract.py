import os
import re
from collections import defaultdict
import sys
import argparse

def parse_hcp_argument(hcp_arg):
    """Parses the HCP range argument."""
    if "-" in hcp_arg:
        return list(map(int, hcp_arg.split("-")))
    else:
        return [int(hcp_arg), int(hcp_arg)]

def calculate_hcp(hand):
    """Calculate the High Card Points (HCP) for a bridge hand."""
    hcp_values = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    total_hcp = 0
    for card in hand:
        total_hcp += hcp_values.get(card, 0)
    return total_hcp

def get_hand_pattern(hand, generic=False):
    """Calculates the hand pattern for a given bridge hand."""
    suits = hand.split(".")
    if len(suits) != 4:
        raise ValueError(f"Invalid hand format: {hand}")
    lengths = [len(suit) for suit in suits]
    separator = "-" if generic else "="
    return separator.join(map(str, sorted(lengths, reverse=True))) if generic else separator.join(map(str, lengths))

def count_opening_patterns_in_file(input_file, pattern_counter, generic=False, hcp_range=None):
    """Reads a file of hands, calculates patterns, and filters by HCP if specified."""
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
        elif line.startswith("[Contract "):
            final_contract = line[11:-2]
        elif auction:
            bids = line.replace("NT", "N").split()
            player_order = ["N", "E", "S", "W"]
            start_index = player_order.index(first_seat)
            rotated_order = player_order[start_index:] + player_order[:start_index]

            for i, bid in enumerate(bids):
                if bid not in ("Pass", "="):  # Ignore "Pass" and "="
                    opening_bid = bid
                    opening_bidder = rotated_order[i % 4]
                    opening_hand = hand_mapping[player_order_dict[first_seat][i % 4]]
                    opening_hcp = calculate_hcp(opening_hand.replace(".", ""))
                    responding_bidder = rotated_order[(i + 2) % 4]
                    responding_hand = hand_mapping[player_order_dict[first_seat][(i + 2) % 4]]
                    responding_hcp = calculate_hcp(responding_hand.replace(".", ""))

                    # Filter hands by HCP range if specified
                    if hcp_range and not (hcp_range[0] <= opening_hcp <= hcp_range[1]):
                        break

                    pattern = get_hand_pattern(opening_hand, generic)
                    if opening_bid in pattern_counter[pattern]:
                        pattern_counter[pattern][opening_bid] += 1
                    else:
                        pattern_counter[pattern]["+"] += 1
                    break
            auction = False

def count_opening_patterns_in_folder(folder_path, filename_pattern, generic=False, hcp_range=None):
    """Processes files in a folder, aggregates pattern counts, and filters by HCP range."""
    pattern_counter = defaultdict(
        lambda: {bid: 0 for bid in [
            "1C", "1D", "1H", "1S", "1N",
            "2C", "2D", "2H", "2S", "2N",
            "3C", "3D", "3H", "3S", "3N",
            "4C", "4D", "4H", "4S", "4N",
            "5C", "5D", "5H", "5S", "5N",
            "+"
        ]}
    )

    if "*" in filename_pattern:
        # If someone enters a RegEx pattern, don't mess with any .* -- this comes through unscathed: '^(?!SCS)\.*'
        filename_pattern = filename_pattern.replace('*', '.*').replace('..*', '.*').lower()
        #print(filename_pattern)
    regex_pattern = re.compile(f"^{filename_pattern}$", re.IGNORECASE)

    matching_files = [
        entry.path for entry in os.scandir(folder_path)
        if entry.is_file() and entry.name.endswith('.pbn') and regex_pattern.match(os.path.splitext(entry.name)[0].lower())
    ]

    if not matching_files:
        print(f"No files matched the pattern: {filename_pattern}")
        return pattern_counter, 0

    for file_path in matching_files:
        print(f"Processing file: {file_path}")
        count_opening_patterns_in_file(file_path, pattern_counter, generic, hcp_range)

    return pattern_counter, len(matching_files)

def display_table(command_line, pattern_counts, generic=False, show_zeros=False):
    """
    Displays the results in a table format with patterns as rows and opening bids as columns.
    """
    headers = [
        "Pattern",
        "1C", "1D", "1H", "1S", "1N",
        "2C", "2D", "2H", "2S", "2N",
        "3C", "3D", "3H", "3S", "3N",
        "4C", "4D", "4H", "4S", "4N",
        "5C", "5D", "5H", "5S", "5N",
        "+", "Total"
    ]
    column_widths = [15] + [5] * (len(headers) - 2) + [6]
    header_row = " ".join(f"{header:>{width}}" for header, width in zip(headers, column_widths))
    title = "---------- Opening Bids by Opening Hand Patterns ----------"
    print("\n" + title.center(sum(column_widths) + len(column_widths) - 1))
    print('\n' + command_line)
    print(header_row)
    print("-" * (sum(column_widths) + len(column_widths) - 1))

    column_totals = {bid: 0 for bid in headers[1:-1]}

    for pattern, counts in sorted(pattern_counts.items()):
        row_total = sum(counts.values())
        row = [
            pattern
        ] + [
            counts[contract] if counts[contract] > 0 or show_zeros else " "
            for contract in headers[1:-1]
        ] + [row_total]
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
    parser = argparse.ArgumentParser(description="Bridge Hand Pattern Analysis")
    parser.add_argument("filename_pattern", help="Filename pattern to process (e.g., '*.pbn')")
    parser.add_argument("--generic", action="store_true", help="Use generic hand patterns (e.g., 4333).")
    parser.add_argument("--hcp", help="Filter results by HCP (e.g., 10 or 10-12).")
    parser.add_argument("--zeros", action="store_true", help="Display zeros instead of spaces for zero values.")
    args = parser.parse_args()

    command_line = " ".join(sys.argv)

    hcp_range = parse_hcp_argument(args.hcp) if args.hcp else None

    pattern_counts, file_count = count_opening_patterns_in_folder(folder_path, args.filename_pattern, args.generic, hcp_range)
    if file_count > 0:
        display_table(command_line, pattern_counts, args.generic, args.zeros)
    else:
        print(f"No .pbn files matched the pattern '{args.filename_pattern}' in the folder '{folder_path}'.")

if __name__ == "__main__":
    main()
