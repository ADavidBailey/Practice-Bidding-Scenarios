@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET scenarioName=%~1

:: Invoke BBA to create a bba file from a pbn file
del P:\bba\%scenarioName%.pbn
BBA --HAND P:\bba\%scenarioName%.pbn --ARCHIVE_FILE P:\bba\%scenarioNamee% --CC1 C:\BBA\GIB-ADB.bbsa --CC2 C:\BBA\GIB-ADB.bbsa --DD 0 --SD 1 --AUTOBID --AUTOCLOSE

:exitbat
