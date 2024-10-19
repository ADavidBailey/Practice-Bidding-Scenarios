@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET inputFilePath=%~dpn1
SET inputFilename=%~n1
SET inputFileFolder=%~dp1

:: Rotate the hands N/S - this will create a PNN file in the same folder
:: with -NS added to the end of the filename:

cscript Z:\Documents\BCScript\2022-06-18\SetDealerMulti.js %inputFilePath%.pbn NS North

:: Move the rotated file to the \bidding-sheets\ folder, and rename to remove the -NS suffix:

move /Y %inputFilePath%-NS.pbn ..\bidding-sheets\%inputFilename%.pbn

:: rename ..\bidding-sheets\%inputFilename%-NS.pbn %inputFilename%.pbn

:: Create a bidding sheets document, with the same name, but BiddingSheets added to the end,
:: and file type .html:

cscript Z:\Documents\BCScript\2022-06-18\BiddingSheets.wsf %inputFileFolder%..\bidding-sheets\%inputFilename%.pbn

:exitbat