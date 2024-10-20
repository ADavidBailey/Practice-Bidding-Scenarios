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
%filter%After_Opp_Overcalls.pbn	 				"Auction [\s\S]+[1234567][CDHS]\s+[1234567]"					%output%After_Opp_Overcalls.pbn	%filter_flag%
%filter%After_Partner_Overcalls.pbn 			"Auction [\s\S]+[1234567][CDHS]\s+[1234567]"					%output%After_Partner_Overcalls.pbn	%filter_flag%

