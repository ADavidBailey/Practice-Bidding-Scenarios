import os

# Read files from pbn folder
PBS_PBN = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios", "pbn")
print(PBS_PBN)

# Write files to pbn-rotated... folder
PBS_PBN_ROTATED = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios", "pbn-rotated-for-4-players")

def rotate_deal(file_path,filename):
     with open(input_file_path, 'r') as file:
        content = file.read()
        processed_text = rotate_hand(content)
        output_file_path = os.path.join(PBS_PBN_ROTATED, filename)

        with open(output_file_path, 'w') as output_file:
            # Save the processed text to the PBS_PBN_ROTATED as a .pbn file
            output_file.write(processed_text)

def rotate_hand(extracted_text):
    processed_text = []
    lines = extracted_text.split('\n')
    processed_text = []
    bN = 0

    for line in lines:
        if line.startswith("[Dealer "):
            bN = bN + 1                           # increment board Number
            bDi = (bN % 4) - 1                    # rotated dealer index (the dDi for North is 0)
            dDealer = line[9]                     # designated dealer is in the input file [Dealer...
            dDi = rotation.index(dDealer)         # designated dealer index, value is  0 to 3
            board_dealer = rotation[bDi]          # the first char of the Deal string
            line = line[:9] + board_dealer + '"]'

        if line.startswith("[Deal "):
            hRi = (4 + bDi - dDi) % 4
            first_hand = rotation[hRi]
            line = line[:7] + first_hand + line[8:]              # rotated deal - 8th character
        processed_text.append(line)
    return '\n'.join(processed_text)

# List all files in the input directory
n_files = 0
rotation = "NESW"
for filename in os.listdir(PBS_PBN):
    input_file_path = os.path.join(PBS_PBN, filename)

    # Check if it's a file and ends with '.pbn'
    if os.path.isfile(input_file_path) and filename.endswith('.pbn'):
        n_files = n_files + 1
        print(str(n_files), filename)
        rotate_deal(input_file_path, filename)
