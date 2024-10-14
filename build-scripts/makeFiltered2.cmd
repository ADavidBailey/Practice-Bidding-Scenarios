ECHO OFF

SET filter=cscript \\Mac\Home\Documents\BCScript\2024-10-03\Filter.js P:\bba\

::
::	If any parameter is passed it, we will save the mismatches, instead of the matches:
::

if "%1"=="" (
	SET output=P:\filtered\
	SET filter_flag=--PDF
) else (
	SET output=P:\filtered-out\
	SET filter_flag=--INVERSE --PDF
)

%filter%Opps_2-Suited_Overcalls.pbn 			"(Note ...Michaels)|(Note ...Unusual)"						%output%Opps_2-Suited_Overcalls.pbn		%filter_flag%

%filter%Two-Suited_Overcalls.pbn				"(Note ...Michaels)|(Note ...Unusual)"						%output%Two-Suited_Overcalls.pbn				%filter_flag%
%filter%Two-Way_Game_Try.pbn					"Note ...Two way game tries"								%output%Two-Way_Game_Try.pbn					%filter_flag%
%filter%Two-Way_New_Minor_Forcing_aka_xyNT.pbn 	"Note ...Two Way New Minor Forcing"							%output%Two-Way_New_Minor_Forcing_aka_xyNT.pbn	%filter_flag%