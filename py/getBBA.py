import argparse
import sys

def end_of_deal():
    result = bidding + this_note
    f.write(board_number.rjust(4) + '  ' + (contract + '-' + declarer).ljust(8)  + score.rjust(5) + '  ' + par.ljust(8) + the_deal + ' | ' + result + '\n')
            
    if result not in results:
        results[result] = 1
    else:
        results[result] += 1


parser = argparse.ArgumentParser(description="get BBA Stats")
parser.add_argument("--input", help="Name of input file")
args = parser.parse_args()
input = args.input

if input[-4:] != '.pbn':
    sys.exit("Input file must be .pbn")
input_file  = '/Users/adavidbailey/Practice-Bidding-Scenarios/bba/' + input

print("reading " + str(input_file))
output_file = '/Users/adavidbailey/Practice-Bidding-Scenarios/bba-summary/' + input + '.txt'
print("writing " + str(output_file))
f = open(output_file, 'w')
f.write(input_file+'\n')

f.write('\n                        -- Sorted by Board Number --\n')
with open(input_file, 'r') as i_file:
    # Split the string into individual lines
    content = i_file.read()
    lines = content.strip().split('\n')

    nBoards = 0  
    nDeals = 0
    nGames = 0
    results = {}
    notes = {}
    this_note = ''
    this_auction = ''
    auction = False
    par = ''
    optimum = False
    f.write('brd# contract score  par     north            east             south            west             | auction...   | notes\n')
    f.write('---- -------- -----  ------  ---------------- ---------------- ---------------- ---------------- | ------------------------- \n')
    for line in lines:
        if line.startswith('[Board'):
            board_number = line[8:-2]
            nBoards += 1
        if line.startswith('[Deal'):
            the_deal = line[9:-2]
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
                # this marks the end of this auction; save the bidding.'
                bidding = '-'.join(this_auction.split()).replace('Pass', 'P').replace('-P-P-P','')
                auction = False
            else:
                this_auction = this_auction + ' ' + line
        if line.startswith('[Auction'):
            # the next line(s) are the auction
            auction = True
        if line.startswith('[Note'):
            note = line[9:-2].capitalize()
            if note not in notes:
                notes[note] = 1
            else:
                notes[note] += 1
            this_note = this_note + ' | ' + note
        if optimum == True:
            txt = line.replace('NT', 'N')
            par = txt[0:3] + txt[4:6].rjust(3)
            optimum = False
        if line.startswith('[Optimum'):
            optimum = True
        if line.strip() == '':
            # I've got everything needed; so, write it out.
            end_of_deal()
            this_note = ''
            this_auction = ''

    if this_auction != '':
        end_of_deal()
    f.write('\n             -- Sorted Summary of Bidding Sequences --\n\n')
    for result in dict(sorted(results.items())):
        txt = str(results[result])
        f.write(txt.rjust(5) + '  ' + result +'\n')

    f.write('\n   -- Sorted Summary of Notes --\n\n')
    for note in dict(sorted(notes.items())):
        txt = str(notes[note])
        f.write(txt.rjust(5) + '  ' + note +'\n')
    
    f.write('\nSummary for ' + input_file + '\n')
    f.write('Deals N/S = ' + str(nDeals) + '\n')
    f.write('Games N/S = ' + str(nGames) + ' or ' + str(round(nGames/nDeals * 100, 2)) + '%\n')
