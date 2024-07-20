# Reads all .pbn files from directory /pbn and makes the statistic lines comments

import os

def scan_for_OptimumResult():

    input_file  = os.path.join(os.path.expanduser("~"), 'Practice-Bidding-Scenarios/BBA/rule18.pbn')
    print(input_file)

    with open(input_file, 'r') as i_file:
        # Split the string into individual lines
        content = i_file.read()
        lines = content.strip().split('\n')
        
        captureNextLine = False
        game = False
        nDeals = 0
        nGames = 0
        for line in lines:
            if captureNextLine == True:
                game = False
                nDeals = nDeals + 1
                words = line.split()
                if words[0] == 'N':
                    if words[1] == 'NT':
                        if words[2]>'8':
                            game = True
                    elif words[1] == 'S' or words[1] == 'H':
                        if words[2] > '9':
                            game = True
                    elif words[1] == 'D' or words[1] == 'C':
                        if words[2] > '10':
                            game = True
                if game == True:
                    nGames = nGames + 1
                captureNextLine = False
                if game == True:
                    print(str(nDeals) + ': ' + line + ' game')
            if line.startswith('[OptimumResult'):
                captureNextLine = True
        print('nDeals = ' + str(nDeals))
        print('nGames = ' + str(nGames))
        print('%Games = ' + str(nGames/nDeals) + '%') 

def main():

    scan_for_OptimumResult()

if __name__ == "__main__":
    main()