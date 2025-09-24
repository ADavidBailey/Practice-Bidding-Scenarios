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

:: file_path doesn't appear to be used.  Should this be removed?
set "file_path=C:\path\to\your\file.txt"

::
::	First, check to see if there is an auction-filter defined in the original .dlr file:
::

call P:\build-scripts\FetchProperty.cmd %scenario% auction-filter

:: echo PropertyValue: "%propertyValue%"


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

echo Filter found: !%filter%!

set this_filter="!%filter%!"

goto foundFilter

:filterNotFound

echo %scenario% doesn't have a filter expression, so no filtered/unfiltered files will be generated
exit /b

:foundFilter

:: ----------------- Replace all \\n with \r?\n --------------------

:: Store the input parameter
set inputString="%this_filter%"

:: Put the chatGPT code after this line ---------------@echo off
::setlocal enabledelayedexpansion

:: Simulated test inputs
rem set "inputString=Auction.....\n1NT Pass 2C.* Pass\n2D"
set "inputString=Auction.....\\n1NT Pass 2C.* Pass\\n2D"
rem (to test real line breaks, paste a multi-line string instead)

:: ---- Decide which case we have ----
set "outputString="

:: Case A: Double-escaped (\\n present)
echo !inputString! | findstr /C:"\\n" >nul
if !errorlevel! equ 0 (
    echo Detected double-escaped \\n
    set "temp=!inputString:\\n=\n!"
    set "outputString=!temp:\n=\r?\n!!"
    goto :done
)

:: Case B: Single-escaped (\n present)
echo !inputString! | findstr /C:"\n" >nul
if !errorlevel! equ 0 (
    echo Detected single-escaped \n
    set "outputString=!inputString:\n=\r?\n!!"
    goto :done
)

:: Case C: Actual multi-line input (no \n at all)
echo Detected real newlines
for /f "tokens=* delims=" %%a in ('echo(!inputString!') do (
    set "line=%%a"
    set "outputString=!outputString!!line!\r?\n!"
)

:done
echo.
echo Input:  !inputString!
echo Output: !outputString!

::endlocal


:: ------------------ Thank You, ChatGPT! --------------------------------

:: echo cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn !outputString! P:\bba-filtered\%scenario%.pbn --PDF /noui
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn "!outputString!" P:\bba-filtered\%scenario%.pbn --PDF /noui >nul
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn "!outputString!" P:\bba-filtered-out\%scenario%.pbn --INVERSE --PDF /noui >nul

endlocal

exit