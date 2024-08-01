import os

def process_file(input_file):
    output_file = input_file + '.txt'
    f = open(output_file, 'w')
    f.write(input_file+'\n')

    with open(input_file, 'r') as i_file:
        # Split the string into individual lines
        content = i_file.read()
        lines = content.strip().split('\n')

        grand_slam = 0
        small_slam = 0
        major_game = 0
        minor_game = 0
        nt_game = 0
        part_score = 0
        other = 0

        notes = {}
        for line in lines:
            cols = line.split(',')
            # 0  1    2     3     4     5    6    7      8     9    10            11       12    13        14
            # ID,Date,Board,North,South,East,West,Result,Score,IMPs,OptimumResult,ParScore,VsPar,DDBidding,DDPlay   
            if cols[0] != 'ID':
                optimum_result = cols[10]
                if optimum_result[3] == 'X':
                    other += 1
                elif optimum_result[1] == '7':
                    grand_slam += 1
                elif optimum_result[1] == '6':
                    small_slam += 1
                elif optimum_result[1:3] == '4H' or optimum_result[1:3] == '4S' or optimum_result[1:3] == '5H' or optimum_result[1:3] == '5S':
                    major_game += 1
                elif optimum_result[1:3] == '5C' or optimum_result[1:3] == '5D':
                    minor_game += 1
                elif optimum_result[1:3] == '3N' or optimum_result[1:3] == '4N' or optimum_result[1:3] == '5N':
                    nt_game += 1
                elif optimum_result[1] == '4' or optimum_result[1] == '3' or optimum_result[1] == '2' or optimum_result[1] == '1':
                    part_score += 1
                else:
                    other += 1
                
                note = cols[13]
                if note not in notes:
                    notes[note] = 0
                notes[note] += 1
                f.write(line + '\n')
        f.write('\nStatistics for ' + input_file + '\n')
        txt = ''
        sum = 0
        for note in notes:
            sum += notes[note]
            txt = ('    ' + str(notes[note]))
            f.write(txt[-5:] + '  ' + note + '\n')
        f.write('_____\n')
        txt = ('    ' + str(sum))
        f.write(txt[-5:] + '  ' + 'TOTAL\n\n')

        f.write('    Par Scores\n')
        f.write('Grand Slam: ' + str(grand_slam).rjust(4) + '\n')
        f.write('Small Slam: ' + str(small_slam).rjust(4) + '\n')
        f.write('Major Game: ' + str(major_game).rjust(4) + '\n')
        f.write('Minor Game: ' + str(minor_game).rjust(4) + '\n')
        f.write('   NT Game: ' + str(nt_game).rjust(4) + '\n')
        f.write('Part Score: ' + str(part_score).rjust(4) + '\n')
        f.write('     Other: ' + str(other).rjust(4) + '\n')
        f.write('           _____\n')
        total = str(grand_slam + small_slam + major_game + minor_game + nt_game + part_score + other)
        f.write('             ' +total[-5:] + '  ' + 'TOTAL\n')
        f.close

folder = '/Users/adavidbailey/Practice-Bidding-Scenarios/BBA/'
files = os.listdir(folder)
for file in files:
    if file[-4:] == '.csv':
        process_file(folder + file)