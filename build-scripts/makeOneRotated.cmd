@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET inputFilePath=%~dpn1
SET inputFilename=%~n1
SET inputFileFolder=%~dp1

:: Rotate the hands N,E,S,W - this will create a PNN file in the same folder
:: with -NESW added to the end of the filename:

cscript S:\SetDealerMulti.js %inputFilePath%.pbn NESW North

:: Move the rotated file to the \pbn-rotated-for-4-players\ folder, and rename to remove the -NESW suffix:

move /Y %inputFilePath%-NESW.pbn ..\pbn-rotated-for-4-players\%inputFilename%.pbn

:: Rotate the hands N/S - this will create a PNN file in the same folder
:: with -NESW added to the end of the filename:

cscript S:\SetDealerMulti.js %inputFilePath%.pbn NESW Dealer NoPBN LIN

:: Move the rotated file to the \lin-rotated-for-4-players\ folder, and rename to remove the -NESW suffix:

move /Y %inputFilePath%-NESW.lin ..\lin-rotated-for-4-players\%inputFilename%.lin

:exitbat