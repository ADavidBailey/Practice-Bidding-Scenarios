input_file  = '/Users/adavidbailey/Practice-Bidding-Scenarios/BBA/Jacoby_2N_Leveled.pbn'
print(input_file)

with open(input_file, 'r') as i_file:
    # Split the string into individual lines
    content = i_file.read()
    lines = content.strip().split('\n')
        
    nDeals = 0
    nGames = 0
    notes = {}
    this_note = ''
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
        if line.startswith('[Note'):
            note = line[9:-2]
            if note not in notes:
                notes[note] = 0
            notes[note] += 1
            if this_note == '':
                this_note = note
            else:
                this_note = this_note + ' | ' + note
        if line.startswith('[Play'):
            print(board + ' ' + declarer + ' ' + contract + ' ' + score + ' | ' + this_note)
            this_note = ''
    print('Statistics for ' + input_file)
    print(' ')
    print('nDeals = ' + str(nDeals))
    print('nGames = ' + str(nGames))
    print('%Games = ' + str((nGames/nDeals) * 100) + '%')
    for note in notes:
        txt = '{:>5} ' + note
        print(txt.format(str(notes[note])))
                         