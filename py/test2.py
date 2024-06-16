import os

pbs = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios")

# List all files in the directory
n_files = 0
for filename in os.listdir(pbs):
    file_path = os.path.join(pbs, filename)
    # Check if it's a file
    if os.path.isfile(file_path):
        print(filename)
        n_files = n_files + 1
print("number of files = " + str(n_files))
