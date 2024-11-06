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

cscript S:\SetDealerMulti.js %iPBN%.pbn Dealer

:: Move the rotated file to the \pbn-rotated-for-4-players\ folder and strip the 
move /Y %iPBN%-NESW.pbn %oPBN%

:: Rotate the hands N,E,S,W - this will create a rotated lin in the temporary folder
cscript S:\SetDealerMulti.js %iPBN% Dealer NoPBN LIN 

:: Move the rotated file to the \lin-rotated-for-4-players\cl folder
move /Y %iPBN%-NESW.pbn %oLIN%

:exitbat
