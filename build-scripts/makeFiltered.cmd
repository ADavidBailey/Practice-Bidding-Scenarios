@echo off

SET filter=cscript /nologo S:\Filter.js P:\bba\

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

SET auction=Auction.....[\s\S][\s\S]?
SET note=Note ...

%filter%1m_1x_2m.pbn							"(%auction%1C[\s\S]+2C)|(%auction%1D[\s\S]+2D)"		%output%1m_1x_2m.pbn				%filter_flag%
%filter%1N_5M_and_6m.pbn 						"%auction%1NT?"										%output%1N_5M_and_6m.pbn			%filter_flag%
%filter%1N_GIB.pbn 								"%auction%1NT?"										%output%1N_GIB.pbn					%filter_flag%

::EXIT

%filter%1N_with_Singleton.pbn 					"%auction%1NT?"										%output%1N_with_Singleton.pbn   	%filter_flag%
%filter%1N.pbn 									"%auction%1NT?"										%output%1N.pbn                  	%filter_flag%
%filter%2N_and_1_Minor.pbn 						"%auction%2NT?"										%output%2N_and_1_Minor.pbn			%filter_flag%
%filter%2N_and_3C_Response.pbn 					"%auction%2NT?\s+Pass\s+3C"							%output%2N_and_3C_Response.pbn		%filter_flag%
%filter%2N_and_Balanced.pbn 					"%auction%2NT?"										%output%2N_and_Balanced.pbn			%filter_flag%
:: 2N_and_MSS.pbn "BBA Not configured for MSS"
%filter%2N_and_Transfers.pbn 					"%auction%2NT?\s+Pass\s+[34][DH]"					%output%2N_and_Transfers.pbn		%filter_flag%
:: 2N_Puppet.pbn "BBA Not Configured for Puppet over 2NT"
:: 2N_Puppet_Leveled.pbn "BBA Not Configured for Puppet over 2NT"
%filter%2N_Smolen.pbn 							"%note%SMOLEN"										%output%2N_Smolen.pbn				%filter_flag%
%filter%2N_Smolen_Leveled.pbn 					"%note%SMOLEN"										%output%2N_Smolen_Leveled.pbn		%filter_flag%
%filter%2NT.pbn 								"%auction%2NT?"										%output%2NT.pbn						%filter_flag%
:: 3_Under_Invitational_Jump.pbn "Not available with BBA
%filter%3N.pbn 									"%auction%3NT?"										%output%3N.pbn						%filter_flag%
%filter%3N_over_LHO_3x.pbn 						"%auction%3[CDHS]\s+Pass\s+Pass\s+3NT?"				%output%3N_over_LHO_3x.pbn			%filter_flag%
%filter%3N_over_RHO_3x.pbn 						"%auction%3[CDHS]\s+3NT?"							%output%3N_over_RHO_3x.pbn			%filter_flag%
%filter%5431_After_NT.pbn 						"%auction%1NT?"										%output%5431_After_NT.pbn			%filter_flag%
%filter%After_1M_2M.pbn 						"(1H.+Pass.+2H)|(1S.+Pass.+2S)"						%output%After_1M_2M.pbn				%filter_flag%
%filter%After_Opp_Overcalls.pbn	 				"%auction%[1234567][CDHS]\s+[1234567]"				%output%After_Opp_Overcalls.pbn		%filter_flag%
%filter%After_Partner_Overcalls.pbn 			"%auction%[1234567][CDHS]\s+[1234567]"				%output%After_Partner_Overcalls.pbn	%filter_flag%
%filter%Any_5422_with_15-17.pbn 				"."													%output%Any_5422_with_15-17.pbn		%filter_flag%
:: Bergen_Raises.pbn "BBA not configured for Bergen raise"
:: Bergen_Thrump_X_after_Preempt.pbn "BBA not configured for Bergen Thrump X"
:: Better_Minor_Lebensohl.pbn "BBA doesn't play this system"
%filter%Dealing_with_Ovecalls_Strong.pbn 		"%auction%[1234567]"								%output%Dealing_with_Ovecalls_Strong.pbn	%filter_flag%
%filter%Dealing_with_Overcalls_Weak.pbn 		"%auction%[1234567]"								%output%Dealing_with_Overcalls_Weak.pbn		%filter_flag%
:: %filter%DONT.pbn "BBA doesn't support DONT"
%filter%Double_Showing_2_Suits.pbn 				"%auction%1[CDHS]+\sPass+\s[12][CDHS]\s+X"			%output%Double_Showing_2_Suits.pbn	%filter_flag%
%filter%Drury.pbn 								"%note%Reverse drury"								%output%Drury.pbn					%filter_flag%
:: Forcing_Pass.pbn "BBA doens't play this(?)"
%filter%Fourth_Suit_Forcing.pbn 				"%note%Fourth suit"									%output%Fourth_Suit_Forcing.pbn		%filter_flag%
%filter%Gambling_3N.pbn							"%note%Gambling"									%output%Gambling_3N.pbn				%filter_flag%
%filter%Game_Forcing_2C.pbn 					"%auction%2C"										%output%Game_Forcing_2C.pbn			%filter_flag%
%filter%Game_Overcalls.pbn 						"%auction%[123][CDHS]\s+(4[HS]|5[CD])"				%output%Game_Overcalls.pbn			%filter_flag%
:: Gavin_3_Under_Invitational_Jump.pbn
:: Gavin_3-Card_Limit_Raise.pbn
:: Gavin_4-Card_Limit_Raise.pbn
:: Gavin_Mixed_Raise.pbn
:: Gavin_Passed_Hand_Response_Structure.pbn
:: Gavin_Semi-Constructive_Raise.pbn
:: Gavin_Semi-Forcing_NT_with_Fit.pbn
:: Gavin_Strong_Splinter.pbn
:: Gavin_Transfers_after_2N_Rebid_Bal.pbn
:: Gavin_Transfers_after_2N_Rebid_Unb.pbn
:: Gavin_Transfers_after_2N_Rebid_Weak.pbn
:: Gavin_Weak_Splinter.pbn
%filter%Gerber_By_Responder.pbn 				"%note%Gerber"										%output%Gerber_By_Responder.pbn		%filter_flag%
%filter%Gerber_By_Opener.pbn 					"%note%Gerber"										%output%Gerber_By_opener.pbn		%filter_flag%
:: Going_for_Blood.pbn
:: Good_Bad_2N.pbn "No one bids 2NT - not sure if this is a script of BBA issue"
%filter%Inverted_Minors.pbn 					"%note%Inverted minors"								%output%Inverted_Minors.pbn			%filter_flag%
%filter%Jacoby_2N.pbn 							"%auction%1[HS]\s+Pass\s+2NT?"						%output%Jacoby_2N.pbn				%filter_flag%
%filter%Jacoby_2N_4x_void.pbn 					"%auction%1[HS]\s+Pass\s+2NT?"						%output%Jacoby_2N_4x_void.pbn		%filter_flag%
%filter%Jacoby_2N_4x_void_Leveled.pbn 			"%auction%1[HS]\s+Pass\s+2NT?"						%output%Jacoby_2N_4x_void_Leveled.pbn %filter_flag%
%filter%Jacoby_2N_Leveled.pbn 					"%auction%1[HS]\s+Pass\s+2NT?"						%output%Jacoby_2N_Leveled.pbn		%filter_flag%
%filter%Jacoby_Super-Accept.pbn 				"%note%Extended acceptance after NT"				%output%Jacoby_Super-Accept.pbn		%filter_flag%
%filter%Jacoby_Transfer.pbn 					"%auction%1NT?\s+Pass\s+(2|4)(H|S)"					%output%Jacoby_Transfer.pbn			%filter_flag%
%filter%Jordan_2N.pbn 							"%auction%1[CDHS]\s+X\s+2NT?"						%output%Jordan_2N.pbn				%filter_flag%
%filter%Jump_Overcalls.pbn 						"(1(C|D)\s+(2|3))|(1H\s+(2|3)S)|(1(H|S)\s+(3|4))"	%output%Jump_Overcalls.pbn			%filter_flag%
:: Kokish_Relay.pbn "BBA doesn't support Kokish"
%filter%Leaping_Michael.pbn 					"%note%Leaping Michaels"							%output%Leaping_Michael.pbn			%filter_flag%
%filter%Lebensohl.pbn 							"%auction%1NT?\s+2[CDHS] \=\d\=\s+[X234]"			%output%Lebensohl.pbn				%filter_flag%
%filter%Lebensohl_Over_Weak_2.pbn 				"%auction%2[DHS]\s+X\s+Pass"						%output%Lebensohl_Over_Weak_2.pbn	%filter_flag%
%filter%Losing_Trick_Count.pbn 					"."													%output%Losing_Trick_Count.pbn			
%filter%Major_Opener.pbn 						"%auction%1[HS]"									%output%Major_Opener.pbn			%filter_flag%
%filter%Major_Suit_Fit.pbn 						"."													%output%Major_Suit_Fit.pbn			%filter_flag%
:: McCabe_after_Weak_2.pbn "BBA doesn't support this convention"
:: McCabe_after_WJO.pbn "BBA doesn't support this convention"
:: Meckwell.pbn "BBA doesn't support this convention"
%filter%Minor_Slams.pbn 						"Contract..(6|7)(C|D)"								%output%Minor_Slams.pbn				%filter_flag%
%filter%Minor_Suit_Opener.pbn 					"%auction%1(C|D)"									%output%Minor_Suit_Opener.pbn		%filter_flag%
:: Minor_Suit_Stayman.pbn "BBA not configured for this convention"
:: Misfit_06-10.pbn
:: Misfit_11-12.pbn
:: Misfit_13-Plus.pbn
:: Misfit.pbn
:: Mitchell_Stayman.pbn
%filter%Mixed_Raise_In_Comp.pbn					"%note%Mixed raise"									%output%Mixed_Raise_In_Comp.pbn		%filter_flag%
:: Multi_2D.pbn "BBA not configured for this convention"
:: Multi_Landy.pbn "BBA doesn't support this convention"
%filter%Namyats_Strong.pbn 						"%auction%4(C|D)"									%output%Namyats_Strong.pbn			%filter_flag%
%filter%Namyats_Weak.pbn 						"%auction%4(H|S)"									%output%Namyats_Weak.pbn			%filter_flag%
:: Ned_2S.pbn
:: Ned_3-Level_Resp_to_1N.pbn
:: Ned_Weak_Two_Leveled.pbn
:: Ned_Weak_Two
%filter%Negative_Double.pbn 					"%auction%1(C|D|H|S)\s+(1|2|3)(C|D|H|S)\s+X"		%output%Negative_Double.pbn			%filter_flag%
:: Negative_Free_Bid.pbn "BBA doesn't support this convention"
%filter%New_Minor_Forcing.pbn					"%note%Two Way New Minor Forcing"					%output%New_Minor_Forcing.pbn		%filter_flag%
:: Non_Leaping_Michaels_After_2-Bid.pbn "BBA doesn't support this convention"
:: Non_Leaping_Michaels_After_3-Bid.pbn "BBA doesn't support this convention"
%filter%Notrump_18-19.pbn 						"."													%output%Notrump_18-19.pbn			%filter_flag%
%filter%Opp_Redoubles.pbn						"%auction%1[CDHSN]T?\s+X\s+XX"						%output%Opp_Redoubles.pbn			%filter_flag%
%filter%Opps_2-Suited_Overcalls.pbn 			"(%note%Michaels)|(%note%Unusual)"					%output%Opps_2-Suited_Overcalls.pbn	%filter_flag%
%filter%Opps_Bid_Over_GF_2C.pbn					"%auction%2C\s+[234X]"								%output%Opps_Bid_Over_GF_2C.pbn		%filter_flag%
%filter%Opps_Double_1_NT.pbn					"%auction%1NT?\s+X"									%output%Opps_Double_1_NT.pbn		%filter_flag%
%filter%Opps_Double_Jacoby.pbn					"%auction%1NT?\s+Pass\s+[24][DH]\s+X"				%output%Opps_Double_Jacoby.pbn		%filter_flag%
%filter%Opps_Double_Stayman.pbn					"%auction%1NT?\s+Pass\s+2C....\s+X"					%output%Opps_Double_Stayman.pbn		%filter_flag%
%filter%Opps_Gambling_3N.pbn 					"%note%Gambling"										%output%Opps_Gambling_3N.pbn		%filter_flag%
:: Opps_Multi_2D.pbn "BBA not configured for this convention"
%filter%Opps_Open_1N_15-17.pbn 					"%auction%1NT?"										%output%Opps_Open_1N_15-17.pbn		%filter_flag%
%filter%Opps_Overcall_1NT.pbn					"%auction%1[CDHS]\s+1NT?"							%output%Opps_Overcall_1NT.pbn		%filter_flag%
%filter%Opps_Overcall_Stayman_or_Jacoby.pbn		"%auction%1NT?\s+Pass\s+[24][CDH]\s+[234]"			%output%Opps_Overcall_Stayman_or_Jacoby.pbn	%filter_flag%
%filter%Opps_Preempt.pbn						"%auction%[2345]"									%output%Opps_Preempt.pbn			%filter_flag%
%filter%Opps_Preemptive_Overcall.pbn 			"(1(C|D)\s+(2|3))|(1H\s+(2|3)S)|(1(H|S)\s+(3|4))"	%output%Opps_Preemptive_Overcall.pbn %filter_flag%
%filter%Opps_Takeout_X.pbn						"%auction%[12][CDHS]\s+X"							%output%Opps_Takeout_X.pbn			%filter_flag%
%filter%Opps_Takeout_X_We_XX.pbn				"%auction%[12][CDHS]\s+X\s+XX"						%output%Opps_Takeout_X_We_XX.pbn	%filter_flag%
%filter%Opps_Weak_Two.pbn 						"%auction%2(D|H|S)"									%output%Opps_Weak_Two.pbn			%filter_flag%
%filter%Overcalls.pbn 							"%auction%1.\s+[12345]"								%output%Overcalls.pbn				%filter_flag%
%filter%Power_Double_Balanced.pbn				"%auction%1.\s+X"									%output%Power_Double_Balanced.pbn	%filter_flag%
%filter%Power_Double_Unbalanced.pbn				"%auction%1.\s+X"									%output%Power_Double_Unbalanced.pbn	%filter_flag%
%filter%Preempt_X_XX.pbn						"%auction%[2345].\s+X\s+XX"							%output%Preempt_X_XX.pbn			%filter_flag%
%filter%Preempts.pbn							"%auction%[2345]"									%output%Preempts.pbn				%filter_flag%
%filter%Responsive_Double.pbn					"%auction%1[CDHS]\s+X\s+[123].[ =123456789]+X"		%output%Responsive_Double.pbn		%filter_flag%
%filter%Reverse_After_Two_Over_One.pbn 			"NoMatches"											%output%Reverse_After_Two_Over_One.pbn	%filter_flag%
%filter%Reverse_By_Opener.pbn 					"%auction%1[CDHS][\s\S]+2"							%output%Reverse_By_Opener.pbn		%filter_flag%
%filter%Reverse_By_Responder.pbn				"%auction%1C\s+Pass\s+1D[\s\S]+\S+\s+Pass\s+2[HS]"	%output%Reverse_By_Responder.pbn	%filter_flag%
:: Robot_Free_Bid.pbn "BBA doesn't support this convention"
%filter%Rule_of_16-15.pbn 						"%auction%1.\s+1NT?"								%output%Rule_of_16-15.pbn			%filter_flag%
%filter%Rule_of_16-16.pbn 						"%auction%1.\s+1NT?"								%output%Rule_of_16-16.pbn			%filter_flag%
%filter%Rule_of_16-17.pbn 						"%auction%1.\s+1NT?"								%output%Rule_of_16-17.pbn			%filter_flag%
%filter%Rule_of_16-18.pbn 						"%auction%1.\s+1NT?"								%output%Rule_of_16-18.pbn			%filter_flag%
%filter%Rule_of_16.pbn 							"%auction%1.\s+1NT?"								%output%Rule_of_16.pbn				%filter_flag%
:: Rule_of_2.pbn "BBA doesn't support this guideline"
%filter%Runout_after_1N_X.pbn					"%auction%1NT?\s+X"									%output%Runout_after_1N_X.pbn		%filter_flag%
:: SCS_1C_3.pbnuit_Resp_5-7.pbn "BBA not condfigured for this convention"
:: SCS_1C_3.pbnuit_Resp.pbn "BBA not condfigured for this convention"
:: SCS_1C_54_Resp.pbn "BBA not condfigured for this convention"
:: SCS_1C_55_Resp.pbn "BBA not condfigured for this convention"
:: SCS_1C_any_0-4_Resp.pbn "BBA not condfigured for this convention"
:: SCS_1C_any_5-7_Resp.pbn "BBA not condfigured for this convention"
:: SCS_1C_any_8plus_Resp.pbn "BBA not condfigured for this convention"
:: SCS_Major_Open_2.pbnuit_Resp.pbn "BBA not condfigured for this convention"
:: SCS_Major_with_2nd_Suit.pbn "BBA not condfigured for this convention"
:: SCS_Two_Clubs.pbn "BBA not condfigured for this convention"
:: Serious.pbn "BBA doesn't support this convention"
:: Size_Asking_Minor_Suit_Stayman.pbn "BBA doesn't support this convention"
%filter%Slam_after_NT.pbn						"%auction%[12]NT?"									%output%Slam_after_NT.pbn							%filter_flag%
%filter%Slam_after_Stayman.pbn					"%auction%[12]NT?\s+Pass\s+2C"						%output%Slam_after_Stayman.pbn						%filter_flag%
%filter%Slam_after_Stayman_or_Jacoby_w30plus.pbn "%auction%1NT?\s+Pass\s+[24][CDH]"					%output%Slam_after_Stayman_or_Jacoby_w30plus.pbn	%filter_flag%
%filter%Slam_after_Stayman_or_Jacoby_w31plus.pbn "%auction%1NT?\s+Pass\s+[24][CDH]"					%output%Slam_after_Stayman_or_Jacoby_w31plus.pbn	%filter_flag%
%filter%Slam_after_Transfer.pbn					"%auction%1NT?\s+Pass\s+[24][DH]"					%output%Slam_after_Transfer.pbn						%filter_flag%
%filter%Smolen.pbn 								"%note%SMOLEN"										%output%Smolen.pbn									%filter_flag%
:: Soloway_Jump_Shift.pbn "BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-1.pbn "BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-2.pbn "BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-3.pbn "BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-4.pbn "BBA not configured for this convention"
:: Spiral_Raise.pbn "BBA doesn't support this convention"
:: Spiral_Raises_with_3.pbn "BBA doesn't support this convention"
%filter%Splinters.pbn 							"%note%Splinter"									%output%Splinters.pbn					%filter_flag%
%filter%Splinters_After_Notrump.pbn				"%note%Splinter"									%output%Splinters_After_Notrump.pbn		%filter_flag%
%filter%Splinters_By_Opener.pbn 				"%note%Splinter"									%output%Splinters_By_Opener.pbn			%filter_flag%
%filter%Stayman.pbn 							"%note%Stayman"										%output%Stayman.pbn						%filter_flag%
%filter%Support_Double.pbn						"%note%Support double"								%output%Support_Double.pbn				%filter_flag%
%filter%Takeout_Double.pbn						"%auction%[1234][CDHS]\s+X"							%output%Takeout_Double.pbn				%filter_flag%
%filter%Texas_or_Jacoby.pbn						"%auction%1NT?\s+Pass\s+[24][DH]"					%output%Texas_or_Jacoby.pbn				%filter_flag%
%filter%Texas_Transfer.pbn						"%note%Texas"										%output%Texas_Transfer.pbn				%filter_flag%
:: Tislevoll_after_Opps_Preempt.pbn
:: Transfers_after_1M_X.pbn
:: Trap_Pass
:: Trap_Pass_Maybe
:: Trap_Pass_Maybe.pbn
:: Trap_Pass.pbn
%filter%Two-Suited_Overcalls.pbn				"(%note%Michaels)|(%note%Unusual)"					%output%Two-Suited_Overcalls.pbn				%filter_flag%
%filter%Two-Way_Game_Try.pbn					"%note%Two way game tries"							%output%Two-Way_Game_Try.pbn					%filter_flag%
%filter%Two-Way_New_Minor_Forcing_aka_xyNT.pbn 	"%note%Two Way New Minor Forcing"					%output%Two-Way_New_Minor_Forcing_aka_xyNT.pbn	%filter_flag%
:: Twoay_Size_Ask.pbn "BBA doesn't support this convention"
%filter%Two_Notrump.pbn 						"%auction%2NT?"										%output%Two_Notrump.pbn							%filter_flag%
%filter%Two_Over_One.pbn						"%auction%1[DHS]\s+Pass\s+2[CDH]"					%output%Two_Over_One.pbn						%filter_flag%
:: Vics_2C_Relay.pbn "BBA doesn't support this convention"
%filter%W2_X_XX.pbn 							"%auction%2(D|H|S)\s+X\s+XX"						%output%W2_X_XX.pbn								%filter_flag%
%filter%We_Overcall.pbn							"%auction%[1234][CDHSN]T?\s+[1234567]"				%output%We_Overcall.pbn							%filter_flag%
%filter%We_Overcall_1N.pbn 						"%auction%1NT?\s+[1234567]"							%output%We_Overcall_1N.pbn						%filter_flag%
%filter%We_X_Opps_Preempt.pbn					"%auction%[234][CDHS]\s+X"							%output%We_X_Opps_Preempt.pbn					%filter_flag%
%filter%We_X_Opps_Weak_2.pbn					"%auction%2[DHS]\s+X"								%output%We_X_Opps_Weak_2.pbn					%filter_flag%
%filter%Weak_2_Bids.pbn							"%auction%2[DHS]"									%output%Weak_2_Bids.pbn							%filter_flag%
%filter%Weak_2_Bids_Lax.pbn						"%auction%2[DHS]"									%output%Weak_2_Bids_Lax.pbn						%filter_flag%
%filter%Weak_2_Bids_Lax_Leveled.pbn				"%auction%2[DHS]"									%output%Weak_2_Bids_Lax_Leveled.pbn				%filter_flag%
%filter%Weak_2_Bids_Leveled.pbn					"%auction%2[DHS]"									%output%Weak_2_Bids_Leveled.pbn					%filter_flag%
:: Weak_NT_09-12.pbn "BBA not configured for this convention"
:: Weak_NT_09-15.pbn "BBA not configured for this convention"
:: Weak_NT_10-12.pbn "BBA not configured for this convention"
:: Weak_NT_10-13.pbn "BBA not configured for this convention"
:: Weak_NT_13-15.pbn "BBA not configured for this convention"
:: Weak_NT_14-15.pbn "BBA not configured for this convention"
:: XYZ.pbn "Unsupported by BBA?"