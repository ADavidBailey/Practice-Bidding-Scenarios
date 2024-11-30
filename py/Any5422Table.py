from collections import defaultdict

def get_hand_pattern(hand):
    """
    Calculates the hand pattern for a given bridge hand.
    Example: AQJ9.J6.AKJ63.T4 -> 4252 (Spades: 4, Hearts: 2, Diamonds: 5, Clubs: 2)
    """
    suits = hand.split(".")  # Split into suits
    return "".join(str(len(suit)) for suit in suits)  # Return pattern as a string

def count_opening_patterns(input_file):
    """
    Reads a file of hands, determines the pattern of each hand,
    and counts the occurrences of each opening bid for each hand pattern.
    Includes all five opening bids: 1S, 1H, 1D, 1C, and 1NT.
    """
    # Initialize a defaultdict to store counts for each hand pattern and opening bid
    pattern_counter = defaultdict(lambda: {"1S": 0, "1H": 0, "1D": 0, "1C": 0, "1NT": 0})
    auction = False
    
    with open(input_file, "r") as infile:
        lines = infile.readlines()

        for line in lines:
            line = line.strip()  # Clean up the line
            if line.startswith("[Deal"):
                deal_line = line
            if auction:
                if line.startswith("1C") or line.startswith("1D") or line.startswith("1H") or line.startswith("1S") or line.startswith("1N"):
                    # Get the hand pattern and count it for the hand pattern
                    hand = deal_line.split()[3]
                    pattern = get_hand_pattern(hand)
                    
                    opening_bid = line.split()[0]  # Get the opening bid (e.g., "1S")
                    pattern_counter[pattern][opening_bid] += 1
                auction = False  # Reset auction flag after processing the bid
            if line.startswith("[Auction"):
                auction = True  # Set auction flag when [Auction] line is found  
    
    return pattern_counter

def display_table(pattern_counts):
    """
    Displays the results in a table format with patterns as rows and opening bids as columns.
    Adds totals for each row and column.
    """
    # Define the table headers
    headers = ["Pattern", "1S", "1H", "1D", "1C", "1NT", "Total"]
    column_widths = [8, 5, 5, 5, 5, 5, 6]
    
    # Print the header row
    header_row = " ".join(f"{header:>{width}}" for header, width in zip(headers, column_widths))
    print(header_row)
    print("-" * sum(column_widths))
    
    # Initialize column totals
    column_totals = {"1S": 0, "1H": 0, "1D": 0, "1C": 0, "1NT": 0}
    
    # Print each row of the table
    for pattern, counts in sorted(pattern_counts.items()):
        row_total = sum(counts.values())  # Total for the row
        row = [pattern] + [counts["1S"], counts["1H"], counts["1D"], counts["1C"], counts["1NT"], row_total]
        formatted_row = " ".join(f"{value:>{width}}" for value, width in zip(row, column_widths))
        print(formatted_row)
        
        # Update column totals
        for bid in column_totals:
            column_totals[bid] += counts[bid]
    
    # Print totals row
    total_row = ["Total"] + [column_totals[bid] for bid in ["1S", "1H", "1D", "1C", "1NT"]] + [sum(column_totals.values())]
    formatted_total_row = " ".join(f"{value:>{width}}" for value, width in zip(total_row, column_widths))
    print("-" * sum(column_widths))
    print(formatted_total_row)

# Example usage
input_file = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba/Jacoby_2N_4x_void_Leveled.pbn"
pattern_counts = count_opening_patterns(input_file)

# Display results in table format
print("Opening Bid Counts by Pattern:")
display_table(pattern_counts)
