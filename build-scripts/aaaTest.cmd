@echo off

:: The number of files for PowerScript programs
$global:nFiles = 2

# /dlr > /pbn
powershell -ExecutionPolicy Bypass -File "P:\build-scripts\makeAllBBA.ps1"

