@echo off
setlocal enabledelayedexpansion

::
:: This script will make one PBN from a P:\pbn\{scenario}.dlr into P:\pbn\{scenario}.pbn

if "%~1"=="" (
    echo Please provide a scenario name.
    exit /b
)

set scenario=%~1

:: Invoke BBO's Dealer to convert dealer code to a PBN file
:: Seed is specified to ensure consistent results it may be changed from time to time
:: Produce 500 deals

P:\dealer P:\dlr\%scenario%.dlr -s 1 -g 40000000 -p 500 -m >P:\pbn\%scenario%.pbn

:exitbat
