# Reads all .pbn files from directory /pbn and makes the statistic lines comments

import os

def scan_for_Score():

    input_file  = os.path.join(os.path.expanduser("~"), 'Practice-Bidding-Scenarios/BBA/rule15.pbn')
    print(input_file)

    with open(input_file, 'r') as i_file:
        # Split the string into individual lines
        content = i_file.read()
        lines = content.strip().split('\n')
        
        nDeals = 0
        nGames = 0
        for line in lines:
            if line.startswith('[Board'):
                board = line[8:-2]
            if line.startswith('[Declarer'):
                declarer = line[11:-2]
            if line.startswith('[Contract'):
                contract = line[11:-2]
            if line.startswith('[Score'):
                if declarer == 'N' or declarer == 'S': 
                    nDeals = nDeals + 1
                    score = line[11:-2]
                    print(board + ' ' + declarer + ' ' + contract + ' ' + score)
                    if int(score)>150:
                        nGames = nGames + 1
        print('nDeals = ' + str(nDeals))
        print('nGames = ' + str(nGames))
        print('%Games = ' + str(nGames/nDeals) + '%') 


scan_for_Score()