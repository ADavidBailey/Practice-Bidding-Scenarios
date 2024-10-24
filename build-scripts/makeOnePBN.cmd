@echo Opps_Overcall_1NT
IF "%~1"=="" ECHO Provide PBN file as parameter 1 (without .pbn)
IF "%~1"=="" goto exitbat

SET inputFilePath=%~dpn1
SET inputFilename=%~n1
SET inputFileFolder=%~dp1

:: Invoke BBO's Dealer to convert dealer code to a PBN file

P:\dealer %inputFilePath%.dlr -s=10232024 >P:\pbn\%inputFilename%.pbn

:exitbat
