@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET ScenarioName=%~1
echo %ScenarioName%

:: Rotate the hands N,E,S,W - this will create a PNN file in the same folder
:: with -NESW added to the end of the filename:

inputFilePath = P:\pbn\%ScenarioName%.pbn
tempFilePath = P:\pbn-rotated-for-4-players\%ScenarioName%-NESW.pbn

cscript S:\SetDealerMulti.js %inputFilePath% %tempFilePath% Dealer NESW

:: Move the rotated file to the \pbn-rotated-for-4-players\ folder, and rename to remove the -NESW suffix:

move /Y %tempFilePath% P:\pbn-rotated-for-4-players\%ScenarioName%.pbn

:: Rotate the hands N/S - this will create a PNN file in the same folder
:: with -NESW added to the end of the filename:

tempFilePath = P:\lin-rotated-for-4-players\%ScenarioName%-NESW.pbn

cscript S:\SetDealerMulti.js P:pbn\%ScenarioName%.pbn P:lin-rotated-for-4-players\%ScenarioName%.lin NESW Dealer NoPBN LIN
:: Move the rotated file to the \lin-rotated-for-4-players\ folder, and rename to remove the -NESW suffix:

move /Y %tempFilePath% ..\lin-rotated-for-4-players\%ScenarioName%.lin

:exitbat