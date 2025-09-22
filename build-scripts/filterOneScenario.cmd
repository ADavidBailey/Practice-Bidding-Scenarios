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

:: Put the chatGPT code after this line ---------------
@echo off
setlocal enabledelayedexpansion

:: Define the input string, simulating newlines with literal "\\n" characters.
set "inputString=Auction.....\\n1NT Pass 2C.* Pass\\n2D"

:: Check if \\n exists in the input string
echo !inputString! | findstr /C:"\\n" >nul
if %errorlevel% equ 0 (
    :: If \\n exists, replace it with \r?\n!
    set "outputString=!inputString!"
    set "outputString=!outputString:\\n=\r?\n!!"
    echo After replacement of \\n: !outputString!
) else (
    :: If no \\n exists, handle actual newlines in the string.
    set "outputString="
    
    :: Loop over each line of the input string.
    for /f "tokens=* delims=" %%a in ('echo(!inputString!') do (
        set "line=%%a"
        
        :: Replace real newlines (line breaks) with \r?\n!
        set "line=!line!\r?\n!"
        
        :: Output each line (debugging output)
        echo Inside loop - Current line: !line!
        
        :: Concatenate the result into outputString
        set "outputString=!outputString!!line!"
    )
    :: After loop debugging
    echo After loop - final outputString: !outputString!
)

:: Display the final result
echo Final outputString after loop: !outputString!

:: ----------------------------------

:: Echo the values of inputString and outputString after all blocks.
echo inputString: !inputString!
echo outputString: !outputString!

::endlocal


:: ------------------ Thank You, ChatGPT! --------------------------------

:: echo cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn !outputString! P:\bba-filtered\%scenario%.pbn --PDF /noui
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn "!outputString!" P:\bba-filtered\%scenario%.pbn --PDF /noui >nul
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn "!outputString!" P:\bba-filtered-out\%scenario%.pbn --INVERSE --PDF /noui >nul

endlocal

exit