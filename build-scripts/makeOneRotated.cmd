@echo off
::IF "%~1"=="" (
::    ECHO Provide PBN filename as parameter 1 (without .pbn)
::    goto exitbat
::)

SET scenarioName=%~1
SET iPBN=P:\pbn\%scenarioName%
SET oPBN=P:\pbn-rotated-for-4-players\%scenarioName%.pbn
SET oLIN=P:\lin-rotated-for-4-players\%scenarioName%.lin

:: Rotate the hands N,E,S,W - this will create rotated files in the same folder
:: create both pbn and lin files in the P:\pbn folder with -NESW.pbn and -NESW.lin appended

cscript S:\SetDealerMulti.js %iPBN%.pbn NESW Dealer /noui >nul
cscript S:\SetDealerMulti.js %iPBN%.pbn NESW Dealer NoPBN LIN /noui >nul

:: Move the rotated files to the {pbn/lin}-rotated-for-4-players\ folders and strip the NESW 
move /Y %iPBN%-NESW.pbn %oPBN% >nul
move /Y %iPBN%-NESW.lin %oLIN% >nul

:exitbat
