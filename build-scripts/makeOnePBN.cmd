@echo off
setlocal enabledelayedexpansion

::
:: This script will make one PBN from a P:\pbn\{scenario}.dlr into P:\pbn\{scenario}.pbn

if "%~1"=="" (
    echo Please provide a scenario name.
    exit /b 1
)

set scenario=%~1

:: Invoke BBO's Dealer to convert dealer code to a PBN file
:: Seed is specified to ensure consistent results it may be changed from time to time
:: Produce 500 deals

:: Change from 40,000,000 to 300,000,000
:: Run dealer and capture stderr to check for errors
P:\dealer P:\dlr\%scenario%.dlr -s 5 -g 300000000 -p 500 -m >P:\pbn\%scenario%.pbn 2>P:\pbn\%scenario%.err

:: Check if dealer reported an error (errors go to stderr)
if %ERRORLEVEL% neq 0 (
    echo Error: dealer failed with exit code %ERRORLEVEL%
    if exist P:\pbn\%scenario%.err type P:\pbn\%scenario%.err
    del P:\pbn\%scenario%.err 2>nul
    del P:\pbn\%scenario%.pbn 2>nul
    exit /b 1
)

:: Check if error file has content (dealer may exit 0 but still have errors)
for %%A in (P:\pbn\%scenario%.err) do if %%~zA gtr 0 (
    echo Error: dealer reported errors:
    type P:\pbn\%scenario%.err
    del P:\pbn\%scenario%.err 2>nul
    del P:\pbn\%scenario%.pbn 2>nul
    exit /b 1
)

:: Clean up empty error file
del P:\pbn\%scenario%.err 2>nul

:exitbat
exit /b 0
