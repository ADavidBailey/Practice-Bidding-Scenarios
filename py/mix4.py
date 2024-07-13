import os
import random

def renumber(board, board_number):
    board_txt = str(board_number)
    dealer_txt = '2341'[board_number%4]
    part_1 = 'qx|o' + board_txt + '|md|' + dealer_txt
    idx1 = board.find('|md|')+1
    idx2 = board.find('|Board ') + 7
    part_2 = board[idx1+4:idx2]
    part_3 = board_txt + '|sv|' +'onebneboebonbone'[board_number-1] + '|pg||'
    return(part_1 + part_2 + part_3)

lin_filename1 = "Dealer-Drury-S.lin"
lin_filename2 = "Dealer-Smolen-S.lin"
lin_filename3 = "Dealer-Trap-Pass-N.lin"
lin_filename4 = "Dealer-Jacoby-2N-S.lin"
out_filename  = "-mixed.lin"
LIN_ROTATED   = os.path.join(os.path.expanduser("~"), "Practice-Bidding-Scenarios/lin-rotated-for-4-players/")

# get all deals for selected scenarios and split into separate strings
with open(os.path.join(LIN_ROTATED, lin_filename1), 'r') as file1:
    content = file1.read()
    boards1 = content.strip().split('\n')
    len1 = len(boards1)
with open(os.path.join(LIN_ROTATED, lin_filename2), 'r') as file2:
    content = file2.read()
    boards2 = content.strip().split('\n')
    len2 = len(boards2)
with open(os.path.join(LIN_ROTATED, lin_filename3), 'r') as file3:
    content = file3.read()
    boards3 = content.strip().split('\n')
    len3 = len(boards3)
    print(len3)
with open(os.path.join(LIN_ROTATED, lin_filename4), 'r') as file4:
    content = file4.read()
    boards4 = content.strip().split('\n')
    len4 = len(boards4)

# get the upper limit for random starting point
maxR = divmod(min(len1,len2,len3,len4), 4)[0] - 2
print(maxR)

# get random starting point & don't exceed the length of the smallest file
r = random.randint(0, maxR)
print(r)

# get four 4-board sets with one deal from each scenario (Dealer NESW)
boards = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
boards[0] = renumber(boards1[r + 0], 1)  # North from 1st scenario
boards[1] = renumber(boards2[r + 1], 2)  # East  from 2nd scenario
boards[2] = renumber(boards3[r + 2], 3)  # South from 4th scenario
boards[3] = renumber(boards4[r + 3], 4)  # West  from 3rd scenario
r = r + 1  # First Dealer is East
boards[4] = renumber(boards2[r + 3], 5)
boards[5] = renumber(boards3[r + 0], 6)
boards[6] = renumber(boards4[r + 1], 7)
boards[7] = renumber(boards1[r + 2], 8)
r = r + 1  # First Dealer is South
boards[8] = renumber(boards3[r + 2], 9)
boards[9] = renumber(boards4[r + 3], 10)
boards[10] = renumber(boards1[r + 0], 11)
boards[11] = renumber(boards2[r + 1], 12)
r = r + 1 # First  Dealer is West
boards[12] = renumber(boards4[r + 1], 13)
boards[13] = renumber(boards1[r + 2], 14)
boards[14] = renumber(boards2[r + 3], 15)
boards[15] = renumber(boards3[r + 0], 16)

with open(os.path.join(LIN_ROTATED, out_filename), 'w') as out_filename:
    # Join the processed lines back into a single string
    result = '\n'.join(boards)
    out_filename.write(result)

