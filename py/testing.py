import sys
import os
import re
from collections import defaultdict
import argparse


def calculate_hcp(hand):
    """Calculate the High Card Points (HCP) for a bridge hand."""
    hcp_values = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    return sum(hcp_values.get(card, 0) for card in hand)


def process_file(file_path, hcp_counter):
    """
    Processes a single PBN file, calculates total HCP for opening and responding hands,
    and updates the HCP counter.
    """
    player_order_dict = {
        "N": ["North", "East", "South", "West"],
        "E": ["East", "South", "West", "North"],
        "S": ["South", "West", "North", "East"],
        "W": ["West", "North", "East", "South"],
    }

    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    hand_mapping = {}
    auction_in_progress = False
    first_seat = None

    for line in lines:
        line = line.strip()
        if line.startswith("[Deal "):
            deal_data = line[7:-2]
            first_hand = deal_data[0]
            hands = deal_data[2:].split(" ")
            hand_mapping = dict(zip(player_order_dict[first_hand], hands))

        elif line.startswith("[Auction "):
            first_seat = line[10]
            auction_in_progress = True

        elif auction_in_progress and not line.startswith("["):
            bids = line.replace("NT", "N").split()
            player_order = ["N", "E", "S", "W"]
            start_index = player_order.index(first_seat)
            rotated_order = player_order[start_index:] + player_order[:start_index]

            for i, bid in enumerate(bids):
                if bid not in ("Pass", "="):  # Skip passes and repeat symbols
                    opening_bidder = rotated_order[i % 4]
                    responding_bidder = rotated_order[(i + 2) % 4]

                    opening_hand = hand_mapping[opening_bidder]
                    responding_hand = hand_mapping[responding_bidder]

                    opening_hcp = calculate_hcp(opening_hand.replace(".", ""))
                    responding_hcp = calculate_hcp(responding_hand.replace(".", ""))
                    total_hcp = opening_hcp + responding_hcp

                    # Debugging log
                    print(f"DEBUG: Incrementing hcp_counter[{total_hcp}] (Current Value: {hcp_counter[total_hcp]})")

                    # Increment the count for this HCP total
                    hcp_counter[total_hcp] += 1
                    break  # Process only the first non-pass bid


def process_folder(folder_path, filename_pattern):
    """
    Processes all PBN files in a folder that match the given filename pattern.
    """
    hcp_counter = defaultdict(int)

    if "*" in filename_pattern:
        filename_pattern = filename_pattern.replace('*', '.*').replace('..*', '.*').lower()
    regex_pattern = re.compile(f"^{filename_pattern}$", re.IGNORECASE)

    matching_files = [
        entry.path for entry in os.scandir(folder_path)
        if entry.is_file() and entry.name.endswith('.pbn') and regex_pattern.match(os.path.splitext(entry.name)[0].lower())
    ]

    if not matching_files:
        print(f"No files matched the pattern: {filename_pattern}")
        return hcp_counter, 0

    for file_path in matching_files:
        print(f"Processing file: {file_path}")
        process_file(file_path, hcp_counter)

    return hcp_counter, len(matching_files)


def display_results(command_line, hcp_counter):
    """
    Displays the results in a table format.
    """
    print("\nResults:")
    print("-" * 40)
    print(f"{'HCP Total':<10}{'Count':<10}")
    print("-" * 40)

    for hcp_total, count in sorted(hcp_counter.items()):
        print(f"{hcp_total:<10}{count:<10}")

    print("-" * 40)
    print(f"Total Entries: {sum(hcp_counter.values())}")


def main():
    folder_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/"
    parser = argparse.ArgumentParser(description="Bridge Hand HCP Analysis")
    #parser.add_argument("folder_path", help="Path to the folder containing PBN files.")
    parser.add_argument("filename_pattern", help="Filename pattern to match (e.g., '*.pbn').")
    args = parser.parse_args()

    command_line = " ".join(sys.argv)
    hcp_counter, file_count = process_folder(folder_path, args.filename_pattern)

    if file_count > 0:
        display_results(command_line, hcp_counter)
    else:
        print(f"No .pbn files matched the pattern '{args.filename_pattern}' in the folder '{args.folder_path}'.")


if __name__ == "__main__":
    main()
