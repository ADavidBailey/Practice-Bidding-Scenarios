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

lin_filename1 = "Drury-S.lin"
lin_filename2 = "Smolen-S.lin"
lin_filename3 = "Trap_Pass-N.lin"
lin_filename4 = "Jacoby_2N-S.lin"
out_filename  = "-mixed.lin"
print(out_filename)
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
with open(os.path.join(LIN_ROTATED, lin_filename4), 'r') as file4:
    content = file4.read()
    boards4 = content.strip().split('\n')
    len4 = len(boards4)

# get the upper limit for random starting point
maxR1 = divmod(len1, 4)[0] - 2
maxR2 = divmod(len2, 4)[0] - 2
maxR3 = divmod(len3, 4)[0] - 2
maxR4 = divmod(len4, 4)[0] - 2

# get random starting point & don't exceed the length of each file
r1 = random.randint(0, maxR1) * 4
r2 = random.randint(0, maxR2) * 4
r3 = random.randint(0, maxR3) * 4
r4 = random.randint(0, maxR4) * 4
print(r1, r2, r3, r4)

# get four 4-board sets with one deal from each scenario (Dealer NESW)
boards = []
boards.append(renumber(boards1[r1 + 0], 1))  # North from 1st scenario
boards.append(renumber(boards2[r2 + 1], 2))  # East  from 2nd scenario
boards.append(renumber(boards3[r3 + 2], 3))  # South from 4th scenario
boards.append(renumber(boards4[r4 + 3], 4))  # West  from 3rd scenario
r1 = r1 + 1  # First Dealer is East
r2 = r2 + 1  # First Dealer is South
r3 = r3 + 1  # First Dealer is West
r4 = r4 + 1  # First Dealer is North
boards.append(renumber(boards2[r2 + 3], 5))
boards.append(renumber(boards3[r3 + 0], 6))
boards.append(renumber(boards4[r4 + 1], 7))
boards.append(renumber(boards1[r1 + 2], 8))
r1 = r1 + 1  # First Dealer is South
r2 = r2 + 1  # First Dealer is West
r3 = r3 + 1  # First Dealer is North
r4 = r4 + 1  # First Dealer is East
boards.append(renumber(boards3[r3 + 2], 9))
boards.append(renumber(boards4[r4 + 3], 10))
boards.append(renumber(boards1[r1 + 0], 11))
boards.append(renumber(boards2[r2 + 1], 12))
r1 = r1 + 1 # First  Dealer is West
r2 = r2 + 1 # First  Dealer is North
r3 = r3 + 1 # First  Dealer is East
r4 = r4 + 1 # First  Dealer is South
boards.append(renumber(boards4[r4 + 1], 13))
boards.append(renumber(boards1[r1 + 2], 14))
boards.append(renumber(boards2[r2 + 3], 15))
boards.append(renumber(boards3[r3 + 0], 16))

with open(os.path.join(LIN_ROTATED, out_filename), 'w') as out_filename:
    # Join the processed lines back into a single string
    result = '\n'.join(boards)
    out_filename.write(result)

