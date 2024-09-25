import argparse
import sys
import re

parser = argparse.ArgumentParser(description="get BBA Stats")
parser.add_argument("--input", help="Name of input file")
args = parser.parse_args()
input = args.input

if input[-4:] != '.pbn':
    sys.exit("Input file must be .pbn")
input_file  = '/Users/adavidbailey/Practice-Bidding-Scenarios/bba/' + input

print("reading " + str(input_file))
output_file = input_file + '.txt'
print("writing " + str(output_file))
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
    auctions = {}
    this_auction = ''
    auction = False
    par = ''
    optimum = False
    f.write('board declarer contract score  par    | notes' + '\n')
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
        if auction == True:
            if line.startswith('['):
                # this marks the end of this auction; now add it to auctions, the 'dictionary of auctions'
                this_auction = '-'.join(this_auction.split()).replace('Pass', 'P').replace('-P-P-P','')
                this_auction = re.sub(r'-=\d=', '', this_auction)

                if this_auction not in notes:
                    notes[this_auction] = 0
                notes[this_auction] += 1
                
                if this_note == '':
                    this_note = this_auction
                else:
                    this_note = this_note + ' | ' + this_auction

                # we're all done with this auction
                auction = False      
            else:
                this_auction = this_auction + ' ' + line
        if line.startswith('[Auction'):
            # the next line(s) are the auction
            auction = True
        if line.startswith('[Note'):
            note = line[9:-2].capitalize()
            if note not in notes:
                notes[note] = 0
            notes[note] += 1
            if this_note == '':
                this_note = note
            else:
                this_note = this_note + ' | ' + note
        if optimum == True:
            par = line.strip()
            optimum = False
        if line.startswith('[Optimum'):
            optimum = True

        if line.strip() == '':
            txt = board.rjust(5) + declarer.rjust(6) + contract.rjust(9) + score.rjust(9) + '  ' + par.ljust(7)
            f.write(txt + '| ' + this_note + '\n')
            this_note = ''
            this_auction = ''

    f.write('Statistics for ' + input_file + '\n')
    f.write('\n')
    f.write('nDeals = ' + str(nDeals) + '\n')
    f.write('nGames = ' + str(nGames) + '\n')
    f.write('%Games = ' + str((nGames/nDeals) * 100) + '%\n')

    
    #f.write('\n --- Notes ---\n')
    #count = 0
    #notes_sorted = dict(sorted(notes.items()))
    #for note in notes_sorted:
    #    count = count + notes[note]
    #    txt = ('    ' + str(notes[note]))
    #    f.write(txt[-5:] + '  ' + note + '\n')
    #f.write ('\nTotal = ' + str(count) + '\n')
