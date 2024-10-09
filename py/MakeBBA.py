# Reads all .pbn files from the /pbn folder and creates command file for running BBA.exe for each file
# creating a corresponding .pbn file in the /bba directory

import os
#import hashlib

def process_file(files):
    nfiles = 0
    for pbn_file in files:
        if pbn_file.lower().endswith('.pbn'):
            hand = " --HAND P:\\pbn\\" + pbn_file
            archive = " --ARCHIVE_FILE P:\\bba\\" + pbn_file[:-4]  # BBA adds .pbn to the end of the archive file
            cc1 = " --CC1 C:\\BBA\\GIB-ADB.bbsa"
            cc2 = " --CC2 C:\\BBA\\GIB-ADB.bbsa"
            the_rest = " --DD 0 --SD 1 --AUTOBID --AUTOCLOSE\n"
          
          # The normal use case is to update the bba files for a few scenarios -- select the ones you want to update
          # and copy/paste the code to DOS command prompt.
          
          # The code appends to the archive file if it already exists; so, we need to delete the file first.
          
            print("del bba\\" + pbn_file[:-4]+ ".pbn", file = print_file)
            print("C:\\BBA\\BBA" + hand + archive + cc1 + cc2 + the_rest, file = print_file)

            nfiles += 1
            #if nfiles > 1:
            #    break

def main():

    PBS_pbn = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/pbn/")

    current_directory_files = os.listdir(PBS_pbn)
    process_file(current_directory_files)

if __name__ == "__main__":
    print_file = open("../makeBBA.cmd", "w")
    main()
