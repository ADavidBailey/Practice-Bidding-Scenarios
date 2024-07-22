input_file  = '/Users/adavidbailey/Practice-Bidding-Scenarios/BBA/Minor_Suit_Opener.pbn'
output_file = input_file[:-3] + 'txt'
f = open(output_file, 'w')
f.write(input_file+'\n')

with open(input_file, 'r') as i_file:
    # Split the string into individual lines
    content = i_file.read()
    lines = content.strip().split('\n')
        
    nDeals = 0
    nGames = 0
    notes = {}
    this_note = ''
    f.write('board declarer contract score | notes' + '\n')
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
            f.write(board + ' ' + declarer + ' ' + contract + ' ' + score + ' | ' + this_note + '\n')
            this_note = ''
    f.write('Statistics for ' + input_file + '\n')
    f.write( '\n')
    f.write('nDeals = ' + str(nDeals) + '\n')
    f.write('nGames = ' + str(nGames) + '\n')
    f.write('%Games = ' + str((nGames/nDeals) * 100) + '%\n')
    for note in notes:
        txt = '{:>5} ' + note
        f.write(txt.format(str(notes[note]) + '\n'))
                         