@echo off
IF "%~1"=="" EffHO Provide PBN file as parameter 1
IF "%~1"=="" goto exitbat

"BridgeComposer.exe" %1 /event "%~2" /save %1

:exitbat