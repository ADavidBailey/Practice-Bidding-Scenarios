# Reads all .dlr files from directory /dlr and create script for running dealerv2 for each file
# generating a matching .pbn file for each .dlr

import os
import hashlib
def calculate_seed(input):
   # Calculate the SHA-256 hash
   hash_object = hashlib.sha256(input.encode())
   hash_bytes = hash_object.digest()

   # Convert the first 4 bytes of the hash to an integer and take modulus
   hash_integer = int.from_bytes(hash_bytes[:4], byteorder='big') % (2**32 - 1)
   return hash_integer

def process_file(files):
    for filename in files:
        if filename.lower().endswith('.dlr'):
            #print(f"# Found file: {filename}")
            seed = calculate_seed(filename)
            output_filename = filename.replace('.dlr', '.pbn')
            #print('D:\\dealer\\dealer E:\\' + filename + ' >F:\\' + output_filename)
            print("P:\\dealer P:\\dlr\\" + filename + " -s=" + str(seed) + " >P:\\pbn\\" + output_filename) 


def scan_for_dlr(directory_path):
    # Use os.listdir() to get files in the current directory only
    current_directory_files = os.listdir(directory_path)
    process_file(current_directory_files)

    print(f"# Scan complete!")

def main():
    #print("# Create dealer script for running dealer, Version 1.0")

    scan_for_dlr("./dlr")

if __name__ == "__main__":
    main()
