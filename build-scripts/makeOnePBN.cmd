@echo off
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET scenarioName=%~1

:: Invoke BBO's Dealer to convert dealer code to a PBN file

P:\dealer P:\dlr\%scenarioName%.dlr -s 0 >P:\pbn\%scenarioName%.pbn

:exitbat
