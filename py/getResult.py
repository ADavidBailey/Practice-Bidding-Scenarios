input_file  = '/Users/adavidbailey/Practice-Bidding-Scenarios/BBA - Drury.pbn'
print(input_file)

with open(input_file, 'r') as i_file:
    # Split the string into individual lines
    content = i_file.read()
    lines = content.strip().split('\n')
        
    nDeals = 0
    nGames = 0
    print('board declarer contract score')
    for line in lines:
        if line.startswith('[Board'):
            board = line[8:-2]
        if line.startswith('[Declarer'):
            declarer = line[11:-2]
        if line.startswith('[Contract'):
            contract = line[11:-2]
        if line.startswith('[Score'):
            score = line[11:-2]
            if declarer == 'N' or declarer == 'S': 
                nDeals = nDeals + 1
                if int(score)>150:
                    nGames = nGames + 1
            print(board + ' ' + declarer + ' ' + contract + ' ' + score)
    print('nDeals = ' + str(nDeals))
    print('nGames = ' + str(nGames))
    print('%Games = ' + str(nGames/nDeals) + '%') 
