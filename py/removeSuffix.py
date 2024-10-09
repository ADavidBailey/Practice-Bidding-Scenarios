# Rename all .dlr files from directory /dlr to remove the dealer suffix.

import os
n_files = 0
PBS_DLR = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/pbn-rotated-for-4-players/")
current_directory_files = os.listdir(PBS_DLR)
for file in current_directory_files:
    if file.lower()[-6] == '-' and file.endswith('.pbn'):
    
        n_files += 1
        n_txt = str(n_files).ljust(4)
        new_file = file[:-6] + file[-4:]
        print(n_txt + " " + new_file)
        os.rename(PBS_DLR + file,PBS_DLR + new_file)
        #if n_files > 2:
        #    break

print(f"# Suffix removed from " + str(n_files) + " files.")