def calculate_hcp(hand):
    """Calculate High Card Points for a given hand."""
    hcp = 0
    for card in hand:
        if card in "AKQJ":
            hcp += {"A": 4, "K": 3, "Q": 2, "J": 1}[card]
    return hcp

def main():
    file_path = "/Users/adavidbailey/Practice-Bidding-Scenarios/bba-filtered/Too_Strong_for_Overcall.pbn"
    deal_count = 0
    auction = False
    passout_count = 0

    hcp_counts = {}

    try:
        with open(file_path, "r") as infile:
            lines = infile.readlines()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return

    for line in lines:
        line = line.strip()
        if line.startswith("[Deal "):
            deal_count += 1
            deal_line = line[9:-2]
            hands = deal_line.split(" ")
            handN = hands[0]
            handE = hands[1]
            handS = hands[2]
            handW = hands[3]

            hcpS = calculate_hcp(handS)

            # Update the count for South's HCP
            if hcpS in hcp_counts:
                hcp_counts[hcpS] += 1
            else:
                hcp_counts[hcpS] = 1

    # Print the results
    print("South Hands by HCP:")
    for hcp, count in sorted(hcp_counts.items()):
        print(f"HCP {hcp}: {count} hands")

if __name__ == "__main__":
    main()
