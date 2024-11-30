import os
from collections import defaultdict

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
    hand_mapping = {}  # Maps player names to hands
    player_order_dict = {
        "N": ["North", "East", "South", "West"],
        "E": ["East", "South", "West", "North"],
        "S": ["South", "West", "North", "East"],
        "W": ["West", "North", "East", "South"]
    }

    try:
        with open(input_file, "r") as infile:
            lines = infile.readlines()
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return

    for line in lines:
        line = line.strip()

        # Parse the deal line
        if line.startswith("[Deal "):
            try:
                deal_line = line[7:-2]
                first_hand = deal_line[0]

                if first_hand not in player_order_dict:
                    print(f"Error: Invalid first hand indicator '{first_hand}' in line: {line}")
                    continue

                hands = deal_line[2:].split(" ")
                if len(hands) != 4:
                    print(f"Error: Unexpected number of hands: {hands} in line: {line}")
                    continue

                # Map the hands to the correct players based on `first_hand`
                hand_mapping = dict(zip(player_order_dict[first_hand], hands))
            except Exception as e:
                print(f"Error parsing deal line: {line} - {e}")
                continue

        # Parse the auction line
        elif line.startswith("[Auction"):
            try:
                first_seat = line[10]
                if first_seat not in player_order_dict:
                    print(f"Error: Invalid first seat '{first_seat}' in line: {line}")
                    continue
                auction = True
            except Exception as e:
                print(f"Error parsing auction line: {line} - {e}")
                auction = False

        # Process the auction sequence
        elif auction:
            try:
                bids = line.split()
                # Define the order of bidders starting with `first_seat`
                player_order = ["N", "E", "S", "W"]
                start_index = player_order.index(first_seat)
                rotated_order = player_order[start_index:] + player_order[:start_index]

                # Map the rotated order to hands
                rotated_hands = [hand_mapping[player_order_dict["N"][i]] for i in range(4)]

                # Process the bids to find the first non-pass bid
                for i, bid in enumerate(bids):
                    if bid not in ("Pass", "="):  # Ignore "Pass" and annotations like "=1="
                        opening_bid = bid
                        opening_bidder = rotated_order[i % 4]
                        opening_hand = hand_mapping[player_order_dict[first_seat][i % 4]]
                        pattern = get_hand_pattern(opening_hand)

                        if opening_bid in pattern_counter[pattern]:
                            pattern_counter[pattern][opening_bid] += 1
                        else:
                            pattern_counter[pattern]["+"] += 1

                        break
            except Exception as e:
                print(f"Error processing auction line: {line} - {e}")
            finally:
                auction = False

def count_opening_patterns_in_folder(folder_path):
    """
    Processes all files in the specified folder and aggregates the pattern counts.
    """
    # Include specific bid levels and lump everything else into "+"
    pattern_counter = defaultdict(lambda: {
        "1S": 0, "1H": 0, "1D": 0, "1C": 0, "1NT": 0,
        "2S": 0, "2H": 0, "2D": 0, "2C": 0, "2NT": 0,
        "3S": 0, "3H": 0, "3D": 0, "3C": 0, "3NT": 0,
        "+": 0  # Anything above level 3
    })
    for entry in os.scandir(folder_path):
        if entry.is_file() and entry.name.endswith(".pbn"):
            print(f"Processing file: {entry.name}")
            count_opening_patterns_in_file(entry.path, pattern_counter)
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
    column_totals = {bid: 0 for bid in headers[1:-1]}  # Track totals for each column
    
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
folder_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/"
pattern_counts = count_opening_patterns_in_folder(folder_path)
print("Opening Bid Counts by Pattern:")
display_table(pattern_counts)
