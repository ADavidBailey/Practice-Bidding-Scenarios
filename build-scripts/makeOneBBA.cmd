@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET inputFilePath=%~dpn1
SET inputFilename=%~n1
SET inputFileFolder=%~dp1

:: ECHO inputFilePath: %inputFilePath%
:: ECHO inputFilename: %inputFilename%
:: ECHO inputFileFolder: %inputFileFolder%

:: Invoke BBA to create a bba file from a pbn file

del P:\bba\%inputFilename%.bba
C:\BBA\BBA --HAND %inputFilePath%.pbn --ARCHIVE_FILE P:\bba\%inputFilename% --CC1 C:\BBA\GIB-ADB.bbsa --CC2 C:\BBA\GIB-ADB.bbsa --DD 0 --SD 1 --AUTOBID --AUTOCLOSE

:exitbat
