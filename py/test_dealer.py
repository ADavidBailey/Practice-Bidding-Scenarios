import os

PBS_PBN = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/", "pbn")
n_files = 0
for filename in os.listdir(PBS_PBN):

    input_file_path = os.path.join(PBS_PBN, filename)

    # Check if it's a file and ends with -X.pbn, where X is N, E, S, W.
    if os.path.isfile(input_file_path) and filename.endswith('.pbn') and filename[-6] == '-':
        n_files = n_files + 1

        # get the dealer from the [Dealer... line in the first record of the file
        with open(input_file_path, 'r') as file:
            content = file.read()
            lines = content.strip().split('\n')
            for line in lines:
                if line.startswith("[Dealer "):
                    dDealer = line[9]
                    break
        if filename[-5] != dDealer:
            print('Error: ' + filename + ' | ' + dDealer)
        else:
            print('OK: ' + filename + ' | ' + dDealer)