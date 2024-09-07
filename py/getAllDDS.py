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

        grand_slam_vs_par = 0
        small_slam_vs_par = 0
        major_game_vs_par = 0
        minor_game_vs_par = 0
        nt_game_vs_par = 0
        part_score_vs_par = 0
        other_vs_par = 0

        notes = {}
        
        for line in lines:
            cols = line.split(',')
            # 0  1    2     3     4     5    6    7      8     9    10        11       12    13        14
            # ID,Date,Board,North,South,East,West,Result,Score,IMPs,ParResult,ParScore,VsPar,DDBidding,DDPlay
            if cols[0] != '#' and cols[0] != 'ID':
                vs_par = int(cols[12])
                optimum_result = '"' + cols[10]
                if optimum_result[3] == 'X':
                    other += 1
                    other_vs_par = other_vs_par + vs_par
                elif optimum_result[1] == '7':
                    grand_slam += 1
                    grand_slam_vs_par = grand_slam_vs_par + vs_par
                elif optimum_result[1] == '6':
                    small_slam += 1
                    small_slam_vs_par = small_slam_vs_par + vs_par
                elif optimum_result[1:3] == '4H' or optimum_result[1:3] == '4S' or optimum_result[1:3] == '5H' or optimum_result[1:3] == '5S':
                    major_game += 1
                    major_game_vs_par = major_game_vs_par + vs_par
                elif optimum_result[1:3] == '5C' or optimum_result[1:3] == '5D':
                    minor_game += 1
                    minor_game_vs_par = minor_game_vs_par + vs_par
                elif optimum_result[1:3] == '3N' or optimum_result[1:3] == '4N' or optimum_result[1:3] == '5N':
                    nt_game += 1
                    nt_game_vs_par = nt_game_vs_par + vs_par
                elif optimum_result[1] == '4' or optimum_result[1] == '3' or optimum_result[1] == '2' or optimum_result[1] == '1':
                    part_score += 1
                    part_score_vs_par = part_score_vs_par + vs_par
                else:
                    other += 1
                    other_vs_par = other_vs_par + vs_par
                
                note = cols[13]
                if note not in notes:
                    notes[note] = 0
                notes[note] += 1
                f.write(line + '\n')
        f.write('\nStatistics for ' + input_file + '\n')
        txt = ''
        sum = 0
        for note in dict(sorted(notes.items())):
            sum += notes[note]
            txt = ('    ' + str(notes[note]))
            f.write(txt[-5:] + '  ' + note + '\n')
        f.write('_____\n')
        txt = ('    ' + str(sum))
        f.write(txt[-5:] + '  ' + 'TOTAL\n\n')

        
        f.write('       --- Par Scores ---\n')
        f.write('            count  vsPar avg\n')
        if grand_slam > 0:
            grand_slam_ratio = round(grand_slam_vs_par / grand_slam, 2)
        else:
            grand_slam_ratio = 1
        f.write('Grand Slam: ' + str(grand_slam).rjust(4) + '     ' + str(grand_slam_ratio).rjust(4) + '\n')

        if small_slam > 0:
            small_slam_ratio = round(small_slam_vs_par / small_slam, 2)
        else:
            small_slam_ratio = 1
        f.write('Small Slam: ' + str(small_slam).rjust(4) + '     ' + str(small_slam_ratio).rjust(4) + '\n')

        if major_game > 0:
            major_game_ratio = round(major_game_vs_par / major_game, 2)
        else:
            major_game_ratio = 1
        f.write('Major Game: ' + str(major_game).rjust(4) + '      ' + str(major_game_ratio).rjust(4) + '\n')

        if minor_game > 0:
            minor_game_ratio = round(minor_game_vs_par / minor_game, 2)
        else:
            minor_game_ratio = 1
        f.write('Minor Game: ' + str(minor_game).rjust(4) + '      ' + str(minor_game_ratio).rjust(4) + '\n')

        if nt_game > 0:
            nt_game_ratio = round(nt_game_vs_par / nt_game, 2)
        else:
            nt_game_ratio = 1
        f.write('   NT Game: ' + str(nt_game).rjust(4) + '      ' + str(nt_game_ratio).rjust(4) + '\n')

        if part_score > 0:
            part_score_ratio = round(part_score_vs_par / part_score, 2)
        else:
            part_score_ratio = 1
        f.write('Part Score: ' + str(part_score).rjust(4) + '      ' + str(part_score_ratio).rjust(4) + '\n')

        if other > 0:
            other_ratio = round(other_vs_par / other, 2)
        else:
            other_ratio = 1
        f.write('     Other: ' + str(other).rjust(4) + '      ' + str(other_ratio).rjust(4) + '\n')

        total = str(grand_slam + small_slam + major_game + minor_game + nt_game + part_score + other)
        f.write('             ' +total[-5:] + '  ' + 'TOTAL\n')
        f.close

folder = '/Users/adavidbailey/Practice-Bidding-Scenarios/BBA/'
files = os.listdir(folder)
for file in files:
    if file[-4:] == '.csv':
        if file.startswith('Jacoby_Si[er-Accept'):
            process_file(folder + file)