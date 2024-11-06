@echo off
::IF "%~1"=="" (
::    ECHO Provide PBN filename as parameter 1 (without .pbn)
::    goto exitbat
::)

SET scenarioName=%~1
SET iPBN=P:\pbn\%scenarioName%
SET oPBN=P:\pbn-rotated-for-4-players\%scenarioName%.pbn
SET oLIN=P:\lin-rotated-for-4-players\%scenarioName%.lin

:: Rotate the hands N,E,S,W - this will create a rotated pbn
:: with -NESW appended to the filename
:: create both pbn and lin files

cscript S:\SetDealerMulti.js %iPBN%.pbn NESW Dealer
cscript S:\SetDealerMulti.js %iPBN%.pbn NESW Dealer NoPBN LIN 

:: Move the rotated files to the {pbn/lin}-rotated-for-4-players\ folders and strip the NESW 
move /Y %iPBN%-NESW.pbn %oPBN%
move /Y %iPBN%-NESW.lin %oLIN%

:exitbat
