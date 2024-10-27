# a Script To Rule Them All

# /PBS > /dlr
python3 P:\py\wExtract.py

# /dlr > /pbn
powershell -ExecutionPolicy Bypass -File "P:\build-scripts\makeAllPBNs.ps1"

# /pbn > /pbn > stats.txt
python3 P:\py\wCommentStats.python3

# /pbn > /pbn-rotated-for-4-players > /lin-rotated-for-4-players
powershell -ExecutionPolicy Bypass -File "P:\build-scripts\makeAllRotated.ps1"

# /pbn > /bba
powershell -ExecutionPolicy Bypass -File "P:\build-scripts\makeAllBBA.ps1"


# /bba > /bba-summary
python3 P:\py\wBbaSummary.py

# /bba > /bba-filtered > filter.log > BBA Filter Rates
P:\build-scripts\makeFiltered

# /bba > /bba-filtered-out
P:\build-scripts\makeFiltered out

# /bba-filtered > /bba-filtered         ? could I put titles in the /PBS
P:\build-scripts\setAllTitle.cmd

# /bba-filtered > /bidding-sheets
powershell -ExecutionPolicy Bypass -File "P:\build-scripts\makeAllBiddingSheets.ps1"
