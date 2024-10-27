@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET scenarioName=%~1
SET inputFilePath=P:\pbn\%scenarioName%.pbn

:: BBA adds the .pbn to the archive
SET outputFilePath=P:\bba\%scenarioName%

:: Invoke BBA to create a bba file from a pbn file
del %outputFilePath%.pbn
BBA --HAND %inputFilePath% --ARCHIVE_FILE %outputFilePath% --CC1 C:\BBA\GIB-ADB.bbsa --CC2 C:\BBA\GIB-ADB.bbsa --DD 0 --SD 1 --AUTOBID --AUTOCLOSE

:exitbat
