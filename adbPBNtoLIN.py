# Reads all .pbn files from the folder /pbn-rotated-for-4-players
# generating a matching .lin file in the folder /lin-rotated-for-4-players 

import os
import endplay.parsers.pbn as pbn
import endplay.parsers.lin as lin

def process_file(files, directory_path):
    n_files = 0
    for i_filename in files:
        if i_filename.lower().endswith('.pbn'):
            n_files = n_files + 1
            print(str(n_files) + " " + i_filename)
            o_filename = i_filename.replace('.pbn', '-R.lin')  # Append -R for Rotated
            out_directory_path = directory_path.replace('pbn', 'lin')

            with open(directory_path + "/" + i_filename, 'r') as i_file:
                boards = pbn.load(i_file)
            with open(out_directory_path + '/' + o_filename, 'w') as o_file:
                lin.dump(boards, o_file)


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
