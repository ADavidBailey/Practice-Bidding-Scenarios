@echo off
IF "%~1"=="" ECHO Provide scenario as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET scenario=%1
SET inputFilePath=P:\bba-filtered\%scenario%
SET inputFilename=%~n1
SET inputFileFolder=P:\bba-filtered\

:: Rotate the hands N/S - this will create a PNN file in the same folder
:: with -NS added to the end of the filename:

cscript /nologo S:\SetDealerMulti.js %inputFilePath%.pbn NS North

:: Move the rotated file to the \bidding-sheets\ folder, and rename to remove the -NS suffix:

move /Y %inputFilePath%-NS.pbn ..\bidding-sheets\%inputFilename%.pbn  >nul

:: Create a bidding sheets document, with the same name, but Bidding Sheets added to the end,
:: and file type .html:

cscript /nologo S:\BiddingSheets.wsf P:\bidding-sheets\%scenario%.pbn

"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf" --page-size Letter --quiet --disable-smart-shrinking "P:\bidding-sheets\%scenario% Bidding Sheets.html" --print-media-type "P:\bidding-sheets\%scenario% Bidding Sheets.pdf"

:exitbat