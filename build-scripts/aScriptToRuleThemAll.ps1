# a Script To Rule Them All

# The number of files for PowerScript programs
$global:nTestFiles = 4

# /PBS > /dlr
python3 P:\py\wExtract.py

# /dlr > /pbn
P:\build-scripts\makeAllPBNs.ps1

# /pbn > /pbn > stats.txt
python3 P:\py\wCommentStats.python3

# /pbn > /pbn-rotated-for-4-players > /lin-rotated-for-4-players
P:\build-scripts\makeAllRotated.ps1"

# /pbn > /bba
P:\build-scripts\makeAllBBA.ps1

python3 P:\py\wBbaSummary.py

# /bba > /bba-filtered > filter.log > BBA Filter Rates
P:\build-scripts\makeFiltered

# /bba > /bba-filtered-out
P:\build-scripts\makeFiltered out

# /bba-filtered > /bba-filtered         ? could I put titles in the /PBS
P:\build-scripts\setAllTitle.cmd

# /bba-filtered > /bidding-sheets
P:\build-scripts\makeAllBiddingSheets.ps1
