
# /PBS > /dlr
P:\py\python3 wExtract.py

# /dlr > /pbn
P:\build-scripts\makeAllPBNs.ps1

# /pbn > /pbn > stats.txt
P:\py\python3 wCommentStats.python3

# /pbn > /pbn-rotated-for-4-players > /lin-rotated-for-4-players
P:\build-scripts\makeAllRotated.ps1

# /pbn > /bba
P:\build-scripts\makeAllBBA.ps1

# /bba > /bba-summary
P:\py\python3 wBbaSummary.py

# /bba > /bba-filtered > filter.log > BBA Filter Rates
P:\build-scripts\makeFiltered

# /bba > /bba-filtered-out
P:\build-scripts\makeFiltered out

# /bba-filtered > /bba-filtered         ? could I put titles in the /PBS
P:\build-scripts\setAllTitle.cmd

# /bba-filtered > /bidding-sheets
P:\build-scripts\makeAllBiddingSheets.ps1