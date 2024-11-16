@echo off

:: Takes parameters:
::
::		p1	Scenario Name (required)
::		p2	Property Name (required)
::
::	Searches P:\dlr\[scenario-name].dlr for [property-name]:
::
::	Defines global variable PropertyValue with the property value found in the file
::
::	Displays an error message if the property is not found.

set PropertyValue=

setlocal enabledelayedexpansion

:: Check if ScenarioName and PropertyName are provided
if "%~1"=="" (
    echo Please provide a ScenarioName as the first parameter.
    exit /b 1
)
if "%~2"=="" (
    echo Please provide a PropertyName as the second parameter.
    exit /b 1
)

:: Set the path based on the provided ScenarioName
set "ScenarioName=%~1"
set "FilePath=P:\dlr\%ScenarioName%.dlr"
set "PropertyName=%~2"

:: Check if the file exists
if not exist "%FilePath%" (
    echo File not found: %FilePath%
    exit /b 1
)

:: Search for PropertyName in the file
for /f "tokens=1* delims=:" %%A in ('findstr /c:"%PropertyName%:" "%FilePath%"') do (
    set "PropertyValue=%%B"

)
:: Trim leading spaces from PropertyValue
for /f "tokens=* delims= " %%A in ("%PropertyValue%") do set "PropertyValue=%%A"

if not defined PropertyValue (
	echo No line with "%PropertyName%:" found in %FilePath% )

:: echo %PropertyName%: "%PropertyValue%"
endlocal & set "PropertyValue=%PropertyValue%"