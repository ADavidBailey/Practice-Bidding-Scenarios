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

def count_final_contracts_by_hcp(input_file, contract_counter):
    """Reads a file, calculates final contracts, and filters by HCP ranges."""
    auction = False
    hand_mapping = {}
    final_contract = None
    player_order_dict = {
        "N": ["North", "East", "South", "West"],
        "E": ["East", "South", "West", "North"],
        "S": ["South", "West", "North", "East"],
        "W": ["West", "North", "East", "South"],
    }

    pass_out_count = 0
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
            auction = True
            print(f"Auction starts with seat: {first_seat}")
        elif line.startswith("[Declarer "):
            declarer = line[11]
        elif line.startswith("[Contract "):
            final_contract = line[11:-2]
        elif auction and final_contract:
            # Do this once for each deal
            auction = False

            # Find the opening bidder -- the first player who bids
            bids = line.replace("NT", "N").split()
            player_order = ["N", "E", "S", "W"]
            start_index = player_order.index(first_seat)
            rotated_order = player_order[start_index:] + player_order[:start_index]
            
            for i, bid in enumerate(bids):
                if bid not in ("Pass", "="):  # Ignore "Pass" and "="
                    opening_bid = bid
                    opening_bidder = rotated_order[i % 4]
                    responding_bidder = rotated_order[(i + 2) % 4]
                    break
                opening_bid = "P"
                opening_bidder = None
                responding_bidder = None

            # Extract opening and responding hands and calculate the combined HCP
            opening_hand = hand_mapping[player_order_dict[first_seat][i % 4]]
            opening_hcp = calculate_hcp(opening_hand.replace(".", ""))
            responding_hand = hand_mapping[player_order_dict[first_seat][(i + 2) % 4]]
            responding_hcp = calculate_hcp(responding_hand.replace(".", ""))
            total_hcp = opening_hcp + responding_hcp

            if declarer == (opening_bidder or responding_bidder):
                # Count the contract by HCP
                contract_counter[total_hcp][final_contract] += 1
            else:
                # Count the contract by -HCP
                contract_counter[-total_hcp][final_contract] += 1

def count_final_contracts_in_folder(folder_path, filename_pattern):
    """Processes files in a folder and aggregates final contract counts by HCP."""
    contract_counter = defaultdict(lambda: defaultdict(int))

    matching_files = [
        entry.path for entry in os.scandir(folder_path)
        if entry.is_file() and entry.name.endswith('.pbn') and re.match(filename_pattern.lower(), entry.name.lower())
    ]

    if not matching_files:
        print(f"No files matched the pattern: {filename_pattern}")
        return contract_counter, 0

    for file_path in matching_files:
        print(f"Processing file: {file_path}")
        count_final_contracts_by_hcp(file_path, contract_counter)

    return contract_counter, len(matching_files)

def display_contract_table(contract_counter, tp=False, zeros=False):
    """Displays contract counts in a table format by HCP/TP and grouped by levels."""
    for hcp, contracts in sorted(contract_counter.items()):
        row_counts = [0] * (len(levels) * len(suits))  # Initialize counts for all contracts
        row_total = 0

        for contract, count in contracts.items():
            level = int(contract[0])  # Extract level (e.g., 4 from "4H")
            suit = contract[1]  # Extract suit (e.g., "H" from "4H")
            column_index = (level - 1) * len(suits) + suits.index(suit)
            row_counts[column_index] += count
            row_total += count

        # Update column totals
        for i, count in enumerate(row_counts):
            total_row_counts[i] += count

        # Print sub-total row if first positive hcp
        if looking_for_positive_hcp and hcp > 0:
            looking_for_positive_hcp = False

            # Print separator line
            print("-" * (sum(column_widths) + len(column_widths) - 1))
            total_row = ["Total"] + [total_row_counts[i] for i in range(len(total_row_counts))] + [sum(total_row_counts.values())]
            formatted_total_row = " ".join(f"{value:>{width}}" for value, width in zip(total_row, column_widths))
            print(formatted_total_row)
            print("-" * (sum(column_widths) + len(column_widths) - 1))
            print(header_row)
            # Start over.  Initializetotal row counts for opener/responder
            total_row_counts = defaultdict(int)  # Totals for each contract column
        # Print row
        row = [hcp] + row_counts + [row_total]
        formatted_row = " ".join(f"{value:>{width}}" for value, width in zip(row, column_widths))
        print(formatted_row)
        #total_row_counts = defaultdict(int)  # Totals for each contract column

    # Print totals row
    total_row = ["Total"] + [total_row_counts[i] for i in range(len(total_row_counts))] + [sum(total_row_counts.values())]
    formatted_total_row = " ".join(f"{value:>{width}}" for value, width in zip(total_row, column_widths))
    print("-" * (sum(column_widths) + len(column_widths) - 1))
    print(formatted_total_row)
    print(header_row)

def main():
    folder_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/"
    parser = argparse.ArgumentParser(description="Bridge Contract Analysis")
    parser.add_argument("filename_pattern", help="Filename pattern to process (e.g., '*.pbn')")
    parser.add_argument("--hcp", help="Filter results by HCP range (e.g., 20-40).")
    args = parser.parse_args()
    contract_counter, file_count = count_final_contracts_in_folder(folder_path, args.filename_pattern)
    if file_count > 0:
        print(f"Processed {file_count} files.")
        display_contract_table(contract_counter)
    else:
        print(f"No .pbn files matched the pattern '{args.filename_pattern}' in the folder '{folder_path}'.")


if __name__ == "__main__":
    main()