@echo off

setlocal enableextensions
 
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET scenarioName=%~1
SET inputFilePath=P:\pbn\%scenarioName%.pbn

:: BBA adds the .pbn to the archive
SET outputFilePath=P:\bba\%scenarioName%

call P:\build-scripts\FetchProperty.cmd %scenarioName% convention-card

IF defined propertyvalue ( SET "conventionCard=%propertyvalue%" ) ELSE ( SET "conventionCard=21GF-DEFAULT" )

:: echo  Scenario: %scenarioName%, ConventionCard: "%conventionCard%"

:: Invoke BBA to create a bba file from a pbn file
del %outputFilePath%.pbn
BBA.exe --HAND %inputFilePath% --ARCHIVE_FILE %outputFilePath% --ARCHIVE_TYPE 4 --CC1 P:\bbsa\%conventionCard%.bbsa --CC2 P:\bbsa\%conventionCard%.bbsa --DD 0 --SD 1 --AUTOBID --AUTOCLOSE > nul

:exitbat
