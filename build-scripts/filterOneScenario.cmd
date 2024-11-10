@echo off
setlocal enabledelayedexpansion enableextensions

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

::
::	First, check to see if there is an auction-filter defined in the original .dlr file:
::

call P:\build-scripts\FetchProperty.cmd %scenario% auction-filter
:: echo PropertyValue: %propertyValue%

IF defined propertyvalue ( 
	SET "this_filter=%propertyvalue%"
	goto foundFilter
)

::
:: Next, check to see if it's defined in the DefineAllFilters.cmd file:
::

findstr /c:"%filter%" "P:\build-scripts\DefineAllScenarioFilters.cmd" >nul

:: Check if the string was found
if %errorlevel% neq 0 goto filterNotFound

call P:\build-scripts\DefineAllScenarioFilters.cmd

:: echo Filter found: !%filter%!

set this_filter=!%filter%!

goto foundFilter

:filterNotFound

echo %scenario% doesn't have a filter expression, so no filtered/unfiltered files will be generated
exit /b

:foundFilter

cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn %this_filter% P:\bba-filtered\%scenario%.pbn --PDF ::/noui >nul
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn %this_filter% P:\bba-filtered-out\%scenario%.pbn --INVERSE --PDF ::/noui >nul

exit /b