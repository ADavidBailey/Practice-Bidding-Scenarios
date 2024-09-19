# Reads all .pbn files from directory /pbn and create command file for running BBA for each file
# generating a matching .pbn file for each .dlr

import os
import hashlib

def process_file(files):
    nfiles = 0
    for pbn_file in files:
        if pbn_file.lower().endswith('.pbn'):
            bba_file = pbn_file.replace('.pbn', '.bba')
            hand = " --HAND P:\\pbn\\" + pbn_file
            archive = " --ARCHIVE_FILE P:\\bba\\" + bba_file
            
            print("P:\\BBA.exe --BBSA_FOLDER C:\\BBA --CC1 GIB-ADB.bbsa --CC2 GIB-ADB.bbsa --DD 0 --SD 1 --AUTOBID" + hand + archive)
            nfiles += 1
            if nfiles >3:
                break

def main():

    PBS_pbn = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/pbn/")
    

    current_directory_files = os.listdir(PBS_pbn)
    process_file(current_directory_files)

if __name__ == "__main__":
    main()
