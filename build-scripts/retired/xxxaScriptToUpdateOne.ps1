# A Script to Update One

@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET inputFilePath=%~dpn1
SET inputFilename=%~n1
SET inputFileFolder=%~dp1

# /PBS > /dlr
python3 P:\py\wExtract.py

# /dlr > /pbn                                                       CHANGE TO makeOnePBN.cmd
P:\build-scripts\makeAllPBNs.ps1

# /pbn > /pbn > stats.txt
python3 P:\py\wCommentStats.python3

# /pbn > /pbn-rotated-for-4-players > /lin-rotated-for-4-players    CHANGE TO makeOneRotated.cmd
P:\build-scripts\makeAllRotated.ps1

# /pbn > /bba                                                       CHANGE TO makeOneBBA.cmd
P:\build-scripts\makeAllBBA.ps1

# /bba > /bba-summary
python3 P:\py\wBbaSummary.py

# /bba > /bba-filtered > filter.log > BBA Filter Rates
P:\build-scripts\makeFiltered

# /bba > /bba-filtered-out
P:\build-scripts\makeFiltered out

# /bba-filtered > /bba-makeFiltered
P:\build-scripts\setOneTitle.cmd

# /bba-filtered > /bidding-sheets                                     CHANGE TO makeOneBiddingSheets.cmd
P:\build-scripts\makeAllBiddingSheets.ps1