# Reads all .pbn files from the folder /pbn-rotated-for-4-players
# generating a matching .lin file in the folder /lin-rotated-for-4-players 

import os
import re

def process_files(files, directory_path):
    n_files = 0
    for i_filename in files:
        if i_filename.lower().endswith('.pbn'):
            n_files = n_files + 1
            print(str(n_files) + " " + i_filename)
            
            o_filename = i_filename.replace('.pbn', '-R.lin')  # Append -R for Rotated
            o_directory_path = directory_path.replace('pbn', 'lin')
            
            with open(directory_path + "/" + i_filename, "r") as i_file:

                output = ''
                event = ''
                date = ''
                content = i_file.read()
            
                lines = content.strip().split('\n')
                for line in lines:
                    if line.startswith('[Event '):
                        if event = '':
                            event = '% ' + re.split('"',line)[1] + '\n'
                            output = event
                        continue
                    if line.startswith('[Date '):
                        if date = '':
                            date = '% ' + re.split('"',line)[1] + '\n'
                            output = output.append(date)
                        continue
                    if line.startswith('[Board '):
                        output = output.append(re.split('"',line)[1])
                        continue
                    if line.startswith('[Dealer '):
                        output = output.append(re.split('"',line)[1])
                        continue
                    if line.startswith('[Deal '):
                        dealText = re.split('"',line)[1]
                        dealer = dealText[0]
                        hands = re.split(' ',dealText[2:-9])
                        getLinDeal(dealer,hands)
                        
                        output = output.append( + '\n')
                        continue
                                       
                                      

            with open(out_directory_path + '/' + o_filename, 'r') as o_file:
                # Split the string into individual lines
                content = o_file.read()
                lines = content.strip().split('\n')

                # Process each line to strip until 'md'
                processed_lines = []
                for line in lines:
                    md_index = line.find('|qx|')
                    if md_index != -1:
                        processed_line = line[md_index:]
                        processed_lines.append(processed_line)

            with open(out_directory_path + '/' + o_filename, 'w') as o_file:
                # Join the processed lines back into a single string
                result = '\n'.join(processed_lines)
                o_file.write(result)

def scan_for_pbn(directory_path):
    # Use os.listdir() to get files in the current directory only
    current_directory_files = os.listdir(directory_path)
    process_file(current_directory_files, directory_path)

    print(f"# Scan complete!")

def main():
    scan_for_pbn("./pbn-rotated-for-4-players")

if __name__ == "__main__":
    main()
