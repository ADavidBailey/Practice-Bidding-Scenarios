@echo off
setlocal enabledelayedexpansion

::
:: This script will filter P:\bba\[{scenario}.pbn into P:\bba-filtered\ and P:\bba-filtered-out\
::
:: It will get the filter string from AllScenarioFilters.cmd.
::
:: p1 is the scenario name, and is required.  It should not have path or file extension.
::

if "%~1"=="" (
    echo Please provide a scenario name.
    exit /b
)

set scenario=%~1
set filter=Filter_%scenario%

set "file_path=C:\path\to\your\file.txt"

:: Initialize FOUND variable to "no"
set "filter_found=no"

:: Search for the string in the file

findstr /c:"%filter%" "P:\build-scripts\DefineAllScenarioFilters.cmd" >nul

:: Check if the string was found
if %errorlevel% equ 0 (
    set "filter_found=yes"
)

if %filter_found%==no (
	echo %scenario% doesn't have a filter expression, so no filtered/unfiltered files will be generated
	exit /b
)

call P:\build-scripts\DefineAllScenarioFilters.cmd

:: Display the result
echo Filter found: !%filter%!

set this_filter=!%filter%!

cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn %this_filter% P:\bba-filtered\%scenario%.pbn --PDF
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn %this_filter% P:\bba-filtered-out\%scenario%.pbn --INVERSE --PDF

exit /b