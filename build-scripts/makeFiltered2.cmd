ECHO OFF

SET filter=cscript \\Mac\Home\Documents\BCScript\2024-10-03\Filter.js P:\bba\

::
::	If any parameter is passed it, we will save the mismatches, instead of the matches:
::

if "%1"=="" (
	SET output=P:\bba-filtered\
	SET filter_flag=--PDF
) else (
	SET output=P:\bba-filtered-out\
	SET filter_flag=--INVERSE --PDF
)
%filter%Gerber_By_Responder.pbn 				"Note ...Gerber"								%output%Gerber_By_Responder.pbn				%filter_flag%
%filter%Gerber_By_Opener.pbn 					"Note ...Gerber"								%output%Gerber_By_opener.pbn				%filter_flag%

