import argparse
import sys

parser = argparse.ArgumentParser(description="get BBA Stats")
parser.add_argument("--input", help="Name of input file")
args = parser.parse_args()
input = args.input

if input[-4:] != '.csv':
    sys.exit("Input file must be .csv")
input_file  = '/Users/adavidbailey/Practice-Bidding-Scenarios/BBA/' + input

print("reading " + str(input_file))
output_file = input_file[:-3] + 'csv.txt'
f = open(output_file, 'w')
f.write(input_file+'\n')

with open(input_file, 'r') as i_file:
    # Split the string into individual lines
    content = i_file.read()
    lines = content.strip().split('\n')
    
    notes = {}
    this_note = ''

    for line in lines:
        cols = line.split(',')   
        if cols[0] != '1':
            board = cols[2]
            result = cols[7]
            score = cols[8]
            par_result = cols[10]
            vs_par = cols[12]
            note = cols[13]
            if note not in notes:
                notes[note] = 0
            notes[note] += 1
            #f.write(board + ' ' + result + ' ' + score + ' ' + par + ' ' + vspar + ' | ' + note + '\n')
        f.write(line + '\n')
    f.write('Statistics for ' + input_file + '\n')
    f.write('\n')
    sum = 0
    for note in notes:
        sum += notes[note]
        txt = ('    ' + str(notes[note]))
        f.write(txt[-5:] + '  ' + note + '\n')
        txt = ('    ' + str(sum))
    f.write('_____\n')
    f.write(txt[-5:] + '  ' + 'TOTAL\n')