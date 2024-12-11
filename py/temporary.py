import os
import re
from collections import defaultdict
import sys
import argparse

def calculate_fit_points(bid, hand):
    """
    Calculates the fit points for a bid and hand.

    Args:
        bid (str): A string representing the bid (e.g., "4S").
        hand (str): A string representing the hand (e.g., "AKQ.JT9...").

    Returns:
        int: The fit points based on the bid and hand.
    """
    
    # There are no fit points if the bid is not a suit
    if bid[1] not in "SHDC":
        return 0
    
    # Required fit_cards
    required_fit_cards = {"S": 3, "H": 3, "D": 4, "C": 5}
    
    # Calculate shortage points
    lengths = [len(suit) for suit in hand.split(".")]
    short_suit_points = sum(5 if length == 0 else 3 if length == 1 else 1 if length == 2 else 0 for length in lengths)

    # Map bid suits to indices
    suit_map = {"S": 0, "H": 1, "D": 2, "C": 3}
    fit_cards = lengths[suit_map[bid[1]]]

    # Calculate fit points -- they cannot exceed the number of fit-cards
    return max(fit_cards, short_suit_points) if fit_cards >= required_fit_cards[bid[1]] else 0


def calculate_length_points(hand):
    """Calculates the length points for a hand."""
    LP = 0
    suits = hand.split(".")
    lengths = [len(suit) for suit in suits]
    for length in lengths:
        suit_LP = length - 4
        if suit_LP > 0:
            LP += suit_LP
    return LP

def calculate_hcp(hand):
    """Calculate the High Card Points (HCP) for a bridge hand."""
    hcp_values = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
    total_hcp = 0
    for card in hand:
        total_hcp += hcp_values.get(card, 0)
    return total_hcp

def count_final_contracts_by_hcp(input_file, contract_counter,tp=False):
    """Reads a file and calculates final contracts."""
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
                    break

            if opening_bid[1] in "CDHSN":
                seat1 = player_order_dict[first_seat][i % 4]
                seat2 = player_order_dict[first_seat][(i + 1) % 4]
                seat3 = player_order_dict[first_seat][(i + 2) % 4]
                seat4 = player_order_dict[first_seat][(i + 3) % 4]

                hand1 = hand_mapping[seat1]
                hand2 = hand_mapping[seat2]
                hand3 = hand_mapping[seat3]
                hand4 = hand_mapping[seat4]

                hcp1 = calculate_hcp(hand1)
                hcp2 = calculate_hcp(hand2)
                hcp3 = calculate_hcp(hand3)
                hcp4 = calculate_hcp(hand4)

                if hcp1 + hcp2 + hcp3 + hcp4 != 40:
                    print(f"Warning: Total HCP is not 40: {hcp1 + hcp2 + hcp3 + hcp4}")

                length_points1 = calculate_length_points(hand1)
                fit_points3 = calculate_fit_points(opening_bid, hand3)
 
                if declarer == (seat1[0] or seat3[0]):
                    total_points = (length_points1 + fit_points3 + hcp1 + hcp3) if tp else (hcp1 + hcp3)
                else:
                    total_points = -(hcp2 + hcp4)

                contract_counter[total_points][final_contract] += 1

def count_final_contracts_in_folder(folder_path, filename_pattern,tp=False):
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
        count_final_contracts_by_hcp(file_path, contract_counter,tp)

    return contract_counter, len(matching_files)

def display_contract_table(contract_counter, tp=False, zeros=False):
    """Displays contract counts in a table format by HCP/TP and grouped by levels."""
    levels = range(1, 8)  # Contract levels 1 through 7
    
    suits = ["C", "D", "H", "S", "N"]
    hcptp = "HCP"
    headersHCP = [hcptp] + [f"{level}{suit}" for level in levels for suit in suits] + ["Total"]
    if tp: hcptp = "TP "
    headersHcpTp = [hcptp] + [f"{level}{suit}" for level in levels for suit in suits] + ["Total"]
    
    column_widths = [6] + [5] * (len(headersHCP) - 2) + [6]
    header_row = " ".join(f"{header:>{width}}" for header, width in zip(headersHCP, column_widths))
    print("\n" + "Final Contracts by Combined HCP/TP -- non-opening side are in descending order".center(sum(column_widths) + len(column_widths) - 1))
    print(header_row)
    print("-" * (sum(column_widths) + len(column_widths) - 1))

    looking_for_positive_hcp = True
    # initialize total row counts for non-opener/responder
    total_row_counts = defaultdict(int)  # Totals for each contract column

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
            header_row = " ".join(f"{header:>{width}}" for header, width in zip(headersHcpTp, column_widths))
            print(header_row)
            # Start over.  Initializetotal row counts for opener/responder
            total_row_counts = defaultdict(int)  # Totals for each contract column
        # Print row
        if hcp < 0: hcp = -hcp
        row = [hcp] + row_counts + [row_total]
        formatted_row = " ".join(f"{value:>{width}}" for value, width in zip(row, column_widths))
        if zeros:
            formatted_row = " ".join(f"{'' if value == 0 else value:>{width}}" for value, width in zip(row, column_widths))
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
    parser.add_argument("--tp", action="store_true", help="Use Total Points (TP) instead of HCP.")
    parser.add_argument("--zeros", action="store_false", help="Print zero values.")
    args = parser.parse_args()
    contract_counter, file_count = count_final_contracts_in_folder(folder_path, args.filename_pattern, args.tp)
    if file_count > 0:
        print(f"Processed {file_count} files.")
        display_contract_table(contract_counter)
    else:
        print(f"No .pbn files matched the pattern '{args.filename_pattern}' in the folder '{folder_path}'.")


if __name__ == "__main__":
    main()