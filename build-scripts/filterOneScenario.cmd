@echo off

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

call P:\build-scripts\DefineAllScenarioFilters.cmd

call set this_filter=%%Filter_%scenario%%%

if %this_filter%=="" (
echo %scenario% doesn't have a filter expression, so no filtered/unfiltered files will be generated
exit /b
)

cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn %this_filter% P:\bba-filtered\%scenario%.pbn --PDF
cscript /nologo S:\Filter.js P:\bba\%scenario%.pbn %this_filter% P:\bba-filtered-out\%scenario%.pbn --INVERSE --PDF

exit /b