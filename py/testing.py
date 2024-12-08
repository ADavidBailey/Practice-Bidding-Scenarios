import os
import re
from collections import defaultdict
import sys
import argparse

def calculate_hcp(hand):
    """Calculate the High Card Points (HCP) for a bridge hand."""
    hcp_values = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    total_hcp = 0
    for card in hand:
        total_hcp += hcp_values.get(card, 0)
    return total_hcp

def count_opening_hcp_in_file(input_file, hcp_counter):
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
        elif line.startswith("[Auction "):
            first_seat = line[10]
            auction = True
        elif line.startswith("[Contract "):
            # this ignores whether the contract is doubled or redoubled
            contract = line[11:13]
        elif auction:
            bids = line.replace("NT", "N").split()
            player_order = ["N", "E", "S", "W"]
            start_index = player_order.index(first_seat)
            rotated_order = player_order[start_index:] + player_order[:start_index]
            for i, bid in enumerate(bids):
                if bid == "Pass":
                    continue
                else:
                    break
                           
            opening_hand = hand_mapping[rotated_order[0]]
            opening_hcp = calculate_hcp(opening_hand.replace(".", ""))
            responding_hand = hand_mapping[player_order_dict[first_seat][(i+2) % 4]]
            responding_hcp = calculate_hcp(responding_hand.replace(".", ""))

            total_hcp = opening_hcp + responding_hcp
            if total_hcp in hcp_counter[total_hcp]:
                 hcp_counter[total_hcp] += 1
            else:
                hcp_counter[total_hcp] = 1
            auction = False

def count_total_hcp_for_hands_in_folder(folder_path, filename_pattern):
    """Processes files in a folder, aggregates pattern counts, and filters by HCP range."""
    pattern_counter = defaultdict(
        lambda: {contract: 0 for contract in [
            "1C", "1D", "1H", "1S", "1N",
            "2C", "2D", "2H", "2S", "2N",
            "3C", "3D", "3H", "3S", "3N",
            "4C", "4D", "4H", "4S", "4N",
            "5C", "5D", "5H", "5S", "5N",
            "6C", "6D", "6H", "6S", "6N",
            "7C", "7D", "7H", "7S", "7N"
        ]}
    )


    if "*" in filename_pattern:
        # If someone enters a RegEx pattern, don't mess with any .* -- this comes through unscathed: '^(?!SCS)\.*'
        filename_pattern = filename_pattern.replace('*', '.*').replace('..*', '.*').lower()
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
        count_opening_hcp_in_file(file_path, pattern_counter)

    return pattern_counter, len(matching_files)

def display_table(command_line, hcp_counts):
    """
    Displays the results in a table format with patterns as rows and opening bids as columns.
    The rows are sorted in descending order of the hand patterns.
    """
    headers = [
        "Pattern",
        "1C", "1D", "1H", "1S", "1N",
        "2C", "2D", "2H", "2S", "2N",
        "3C", "3D", "3H", "3S", "3N",
        "4C", "4D", "4H", "4S", "4N",
        "5C", "5D", "5H", "5S", "5N",
        "6C", "6D", "6H", "6S", "6N",
        "7C", "7D", "7H", "7S", "7N", "Total"
    ]
    column_widths = [11] + [5] * (len(headers) - 2) + [6]
    header_row = " ".join(f"{header:>{width}}" for header, width in zip(headers, column_widths))
    title = "---------- Final Contracts by Combined Hand Patterns ----------"
    print("\n" + title.center(sum(column_widths) + len(column_widths) - 1))
    print('\n' + command_line)
    print(header_row)
    print("-" * (sum(column_widths) + len(column_widths) - 1))
    
    column_totals = {contract: 0 for contract in headers[1:-1]}

    row = [display_pattern] + [counts[contract] if counts[contract] > 0 else " " for contract in headers[1:-1]] + [row_total]

    formatted_row = " ".join(f"{value:>{width}}" for value, width in zip(row, column_widths))
    print(formatted_row)

    for contract in column_totals:
        column_totals[contract] += counts[contract]

    total_row = ["Total"] + [column_totals[contract] for contract in headers[1:-1]] + [sum(column_totals.values())]
    formatted_total_row = " ".join(f"{value:>{width}}" for value, width in zip(total_row, column_widths))
    print("-" * (sum(column_widths) + len(column_widths) - 1))
    print(formatted_total_row)
    print(header_row)

def parse_hcp_argument(hcp_arg):
    """Parses the HCP range argument."""
    if "-" in hcp_arg:
        return list(map(int, hcp_arg.split("-")))
    else:
        return [int(hcp_arg), int(hcp_arg)]

def main():
    folder_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/"
    parser = argparse.ArgumentParser(description="Bridge Hand Pattern Analysis")
    parser.add_argument("filename_pattern", help="Filename pattern to process (.pbn is appended automatically).")
    args = parser.parse_args()

    command_line = " ".join(sys.argv)

    hcp_counts, file_count = count_total_hcp_for_hands_in_folder(folder_path, args.filename_pattern)
    if file_count > 0:
        display_table(command_line, hcp_counts)
    else:
        print(f"No .pbn files matched the pattern '{args.filename_pattern}' in the folder '{folder_path}'.")

if __name__ == "__main__":
    main()
