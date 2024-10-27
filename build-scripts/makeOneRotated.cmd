::@echo off
IF "%~1"=="" (
    ECHO Provide PBN filename as parameter 1 (without .pbn)
    goto exitbat
)

SET scenarioName=%~1
SET tempFilePath=P:\temporary\temp
SET inputFilePath=P:\pbn\%scenarioName%.pbn

echo inputFilePath is %inputFilePath% tempFilePath is %tempFilePath%

:: Rotate the hands N,E,S,W - this will create a rotated pbn in the temporary folder
cscript S:\SetDealerMulti.js %inputFilePath% %tempFilePath%.pbn NESW Dealer

:: Move the rotated file to the \pbn-rotated-for-4-players\ folder
move /Y %tempFilePath%.pbn P:\pbn-rotated-for-4-players\%scenarioName%.pbn

:: Rotate the hands N,E,S,W - this will create a rotated lin in the temporary folder
cscript S:\SetDealerMulti.js %inputFilePath% %tempFilePath%.lin NESW Dealer NoPBN LIN

:: Move the rotated file to the \lin-rotated-for-4-players\cl folder
move /Y %tempFilePath%.lin P:\lin-rotated-for-4-players\%scenarioName%.lin

:exitbat
