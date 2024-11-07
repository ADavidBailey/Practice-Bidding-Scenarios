import os
import endplay.parsers.pbn as pbn
import endplay.parsers.lin as lin

def process_file(pbn_files):    
    n_files = 0
    for pbn_filename in pbn_files:
        if pbn_filename.lower().endswith('.pbn'):
            n_files = n_files + 1
            print(str(n_files) + " " + pbn_filename)
            lin_filename = pbn_filename.replace('.pbn', '.lin')
            lin_filepath = os.path.join(LIN_ROTATED, lin_filename)
            print(lin_filepath)

            with open(os.path.join(PBN_ROTATED, pbn_filename), 'r') as pbn_file:
                boards = pbn.load(pbn_file)
            with open(lin_filepath, 'w') as lin_file:
                lin.dump(boards, lin_file)

            with open(lin_filepath, 'r') as lin_file:
                # Split the string into individual lines
                content = lin_file.read()
                lines = content.strip().split('\n')

                # Process each line to strip until 'md', prepend 'qx|o~~~' (~~~ is the board number)
                processed_lines = []
                for line in lines:
                    md_index = line.find('|md|')
                    if md_index != -1:
                        # get the board numberidx = line.find('|Board ') + 7
                        idx = line.find('|Board ') + 7
                        txt = line[idx:]
                        idx = txt.find('|sv|')
                        boardNumber = txt[:idx]

                        processed_line = 'qx|o' + boardNumber + line[md_index:]
                        processed_lines.append(processed_line)

            with open(lin_filepath, 'w') as lin_file:
                # Join the processed lines back into a single string
                result = '\n'.join(processed_lines)
                lin_file.write(result)

def scan_for_pbn():
    # Use os.listdir() to get files in the current directory only
    pbn_files = os.listdir(PBN_ROTATED)
    process_file(pbn_files)

    print(f"# Scan complete!")

PBN_ROTATED = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/pbn-rotated-for-4-players")
LIN_ROTATED = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/lin-rotated-for-4-players")
scan_for_pbn()
