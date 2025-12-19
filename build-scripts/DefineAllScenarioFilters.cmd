@echo off
::
::	Defines regular expression filters for all Scenarios
::
::	Parameters:
::
::		ForceRefresh - Forces the redefinition of the filters, even if they are already present
::					 - Any value for the parameter forces a refresh
::
::	If they are already defined, they won't be normally be redefined.
::	However, if parameter 1 is present, everything will be redefined regardless.

:: If the refresh parameter is specified, define the filters

IF not "%1%"=="" GOTO DefineFilters

:: If Filter_3N isn't defined, define the filters:

IF "%Filter_3N%"=="" GOTO DefineFilters

:: Otherwise, don't redefine the filters:

GOTO AllDone

:DefineFilters

ECHO Defining Filters...

SET auction=Auction.....[\s\S][\s\S]?
SET note=Note ...

SET Filter_1m_1x_2m="(%auction%1C[\s\S]+2C)|(%auction%1D[\s\S]+2D)"
SET Filter_1N_5M_and_6m="%auction%1NT?"
SET Filter_1N_GIB="%auction%1NT?"
SET Filter_1N_with_Singleton="%auction%1NT?"
SET Filter_1N="%auction%1NT?"
SET Filter_2N_and_1_Minor="%auction%2NT?"
SET Filter_2N_and_3C_Response="%auction%2NT?\s+Pass\s+3C"
SET Filter_2N_and_Balanced="%auction%2NT?"
:: 2N_and_MSS="BBA Not configured for MSS"
SET Filter_2N_and_Transfers="%auction%2NT?\s+Pass\s+[34][DH]"
:: 2N_Puppet="BBA Not Configured for Puppet over 2NT"
:: 2N_Puppet_Leveled="BBA Not Configured for Puppet over 2NT"
SET Filter_2N_Smolen="%note%SMOLEN"
SET Filter_2N_Smolen_Leveled="%note%SMOLEN"
SET Filter_2NT="%auction%2NT?"
:: 3_Under_Invitational_Jump="Not available with BBA
SET Filter_3N="%auction%3NT?"
SET Filter_3N_over_LHO_3x="%auction%3[CDHS]\s+Pass\s+Pass\s+3NT?"
SET Filter_3N_over_RHO_3x="%auction%3[CDHS]\s+3NT?"
SET Filter_5431_After_NT="%auction%1NT?"
SET Filter_After_1M_2M="(1H.+Pass.+2H)|(1S.+Pass.+2S)"
SET Filter_After_Opp_Overcalls="%auction%[1234567][CDHS]\s+[1234567]"
SET Filter_After_Partner_Overcalls="%auction%[1234567][CDHS]\s+[1234567]"
SET Filter_Any_5422_with_15-17="."
:: Bergen_Raises="BBA not configured for Bergen raise"
:: Bergen_Thrump_X_after_Preempt="BBA not configured for Bergen Thrump X"
:: Better_Minor_Lebensohl="BBA doesn't play this system"
SET Filter_Dealing_with_Ovecalls_Strong="%auction%[1234567]"
SET Filter_Dealing_with_Overcalls_Weak="%auction%[1234567]"
SET Filter_DONT="%auction%1N +[X2]"
:: DONT="BBA doesn't support DONT"
SET Filter_Double_Showing_2_Suits="%auction%1[CDHS]+\sPass+\s[12][CDHS]\s+X"
SET Filter_Drury="%note%Reverse drury"
:: Forcing_Pass="BBA doens't play this(?)"
SET Filter_Fourth_Suit_Forcing="%note%Fourth suit"
SET Filter_Fourth_Bid_Inviting="(1[CDHS].*Pass.*1[DHSN].*Pass\n.*Pass.*(2NT|3[CDHS])|Two way game tries)"
SET Filter_Gambling_3N="%note%Gambling"
SET Filter_Game_Forcing_2C="%auction%2C"
SET Filter_Game_Overcalls="%auction%[123][CDHS]\s+(4[HS]|5[CD])"
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
SET Filter_Gerber_By_Responder="%note%Gerber"
SET Filter_Gerber_By_Opener="%note%Gerber"
:: Going_for_Blood.pbn
:: Good_Bad_2N="No one bids 2NT - not sure if this is a script of BBA issue"
SET Filter_Inverted_Minors="%note%Inverted minors"
SET Filter_Jacoby_2N="%auction%1[HS]\s+Pass\s+2NT?"
SET Filter_Jacoby_2N_4x_void="%auction%1[HS]\s+Pass\s+2NT?"
SET Filter_Jacoby_2N_4x_void_Leveled="%auction%1[HS]\s+Pass\s+2NT?"
SET Filter_Jacoby_2N_Leveled="%auction%1[HS]\s+Pass\s+2NT?"
SET Filter_Jacoby_Super-Accept="%note%Extended acceptance after NT"
SET Filter_Jacoby_Transfer="%auction%1NT?\s+Pass\s+(2|4)(H|S)"
SET Filter_Jordan_2N="%auction%1[CDHS]\s+X\s+2NT?"
SET Filter_Jump_Overcalls="(1(C|D)\s+(2|3))|(1H\s+(2|3)S)|(1(H|S)\s+(3|4))"
:: Kokish_Relay="BBA doesn't support Kokish"
SET Filter_Leaping_Michael="%note%Leaping Michaels"
SET Filter_Lebensohl="%auction%1NT?\s+2[CDHS] \=\d\=\s+[X234]"
SET Filter_Lebensohl_Over_Weak_2="%auction%2[DHS]\s+X\s+Pass"
SET Filter_Losing_Trick_Count="."
SET Filter_Major_Opener="%auction%1[HS]"
SET Filter_Major_Suit_Fit="."
:: McCabe_after_Weak_2="BBA doesn't support this convention"
:: McCabe_after_WJO="BBA doesn't support this convention"
:: Meckwell="BBA doesn't support this convention"
SET Filter_Minor_Slams="Contract..(6|7)(C|D)"
SET Filter_Minor_Suit_Opener="%auction%1(C|D)"
:: Minor_Suit_Stayman="BBA not configured for this convention"
:: Misfit_06-10.pbn
:: Misfit_11-12.pbn
:: Misfit_13-Plus.pbn
:: Misfit.pbn
:: Mitchell_Stayman.pbn
SET Filter_Mixed_Raise_In_Comp="%note%Mixed raise"
:: Multi_2D="BBA not configured for this convention"
:: Multi_Landy="BBA doesn't support this convention"
SET Filter_Namyats_Strong="%auction%4(C|D)"
SET Filter_Namyats_Weak="%auction%4(H|S)"
:: Ned_2S.pbn
:: Ned_3-Level_Resp_to_1N.pbn
:: Ned_Weak_Two_Leveled.pbn
:: Ned_Weak_Two
SET Filter_Negative_Double="%auction%1(C|D|H|S)\s+(1|2|3)(C|D|H|S)\s+X"
:: Negative_Free_Bid="BBA doesn't support this convention"
SET Filter_New_Minor_Forcing="%note%Two Way New Minor Forcing"
:: Non_Leaping_Michaels_After_2-Bid="BBA doesn't support this convention"
:: Non_Leaping_Michaels_After_3-Bid="BBA doesn't support this convention"
SET Filter_Notrump_18-19="."
SET Filter_Opp_Redoubles="%auction%1[CDHSN]T?\s+X\s+XX"
SET Filter_Opps_2-Suited_Overcalls="(%note%Michaels)|(%note%Unusual)"
SET Filter_Opps_Bid_Over_GF_2C="%auction%2C\s+[234X]"
SET Filter_Opps_Double_1_NT="%auction%1NT?\s+X"
SET Filter_Opps_Double_Jacoby="%auction%1NT?\s+Pass\s+[24][DH]\s+X"
SET Filter_Opps_Double_Stayman="%auction%1NT?\s+Pass\s+2C....\s+X"
SET Filter_Opps_Gambling_3N="%note%Gambling"
:: Opps_Multi_2D="BBA not configured for this convention"
SET Filter_Opps_Open_1N_15-17="%auction%1NT?"
SET Filter_Opps_Overcall_1NT="%auction%1[CDHS]\s+1NT?"
SET Filter_Opps_Overcall_Stayman_or_Jacoby="%auction%1NT?\s+Pass\s+[24][CDH]\s+[234]"
SET Filter_Opps_Preempt="%auction%[2345]"
SET Filter_Opps_Preemptive_Overcall="(1(C|D)\s+(2|3))|(1H\s+(2|3)S)|(1(H|S)\s+(3|4))"
SET Filter_Opps_Takeout_X="%auction%[12][CDHS]\s+X"
SET Filter_Opps_Takeout_X_We_XX="%auction%[12][CDHS]\s+X\s+XX"
SET Filter_Opps_Weak_Two="%auction%2(D|H|S)"
SET Filter_Overcalls="%auction%1.\s+[12345]"
SET Filter_Power_Double_Balanced="%auction%1.\s+X"
SET Filter_Power_Double_Unbalanced="%auction%1.\s+X"
SET Filter_Preempt_X_XX="%auction%[2345].\s+X\s+XX"
SET Filter_Preempts="%auction%[2345]"
SET Filter_Responsive_Double="%auction%1[CDHS]\s+X\s+[123].[ =123456789]+X"
SET Filter_Reverse_After_Two_Over_One="NoMatches"
SET Filter_Reverse_By_Opener="%auction%1[CDHS][\s\S]+2"
SET Filter_Reverse_By_Responder="%auction%1C\s+Pass\s+1D[\s\S]+\S+\s+Pass\s+2[HS]"
:: Robot_Free_Bid="BBA doesn't support this convention"
SET Filter_Rule_of_16-15="%auction%1.\s+1NT?"
SET Filter_Rule_of_16-16="%auction%1.\s+1NT?"
SET Filter_Rule_of_16-17="%auction%1.\s+1NT?"
SET Filter_Rule_of_16-18="%auction%1.\s+1NT?"
SET Filter_Rule_of_16="%auction%1.\s+1NT?"
:: Rule_of_2="BBA doesn't support this guideline"
SET Filter_Runout_after_1N_X="%auction%1NT?\s+X"
:: SCS_1C_3.pbnuit_Resp_5-7="BBA not condfigured for this convention"
:: SCS_1C_3.pbnuit_Resp="BBA not condfigured for this convention"
:: SCS_1C_54_Resp="BBA not condfigured for this convention"
:: SCS_1C_55_Resp="BBA not condfigured for this convention"
:: SCS_1C_any_0-4_Resp="BBA not condfigured for this convention"
:: SCS_1C_any_5-7_Resp="BBA not condfigured for this convention"
:: SCS_1C_any_8plus_Resp="BBA not condfigured for this convention"
:: SCS_Major_Open_2.pbnuit_Resp="BBA not condfigured for this convention"
:: SCS_Major_with_2nd_Suit="BBA not condfigured for this convention"
:: SCS_Two_Clubs="BBA not condfigured for this convention"
:: Serious="BBA doesn't support this convention"
:: Size_Asking_Minor_Suit_Stayman="BBA doesn't support this convention"
SET Filter_Slam_after_NT="%auction%[12]NT?"
SET Filter_Slam_after_Stayman="%auction%[12]NT?\s+Pass\s+2C"
SET Filter_Slam_after_Stayman_or_Jacoby_w30plus="%auction%1NT?\s+Pass\s+[24][CDH]"
SET Filter_Slam_after_Stayman_or_Jacoby_w31plus="%auction%1NT?\s+Pass\s+[24][CDH]"
SET Filter_Slam_after_Transfer="%auction%1NT?\s+Pass\s+[24][DH]"
SET Filter_Smolen="%note%SMOLEN"
:: Soloway_Jump_Shift="BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-1="BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-2="BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-3="BBA not configured for this convention"
:: Soloway_Jump_Shift-Type-4="BBA not configured for this convention"
:: Spiral_Raise="BBA doesn't support this convention"
:: Spiral_Raises_with_3="BBA doesn't support this convention"
SET Filter_Splinters="%note%Splinter"
SET Filter_NT_Splinter="%note%Splinter"
SET Filter_Splinters_By_Opener="%note%Splinter"
SET Filter_Stayman="%note%Stayman"
SET Filter_Support_Double="%note%Support double"
SET Filter_Takeout_Double="%auction%[1234][CDHS]\s+X"
SET Filter_Texas_or_Jacoby="%auction%1NT?\s+Pass\s+[24][DH]"
SET Filter_Texas_Transfer="%note%Texas"
:: Tislevoll_after_Opps_Preempt.pbn
:: Transfers_after_1M_X.pbn
:: Trap_Pass
:: Trap_Pass_Maybe
:: Trap_Pass_Maybe.pbn
:: Trap_Pass.pbn
SET Filter_Two-Suited_Overcalls="(%note%Michaels)|(%note%Unusual)"
SET Filter_Two-Way_Game_Try="%note%Two way game tries"
SET Filter_Two-Way_New_Minor_Forcing_aka_xyNT="%note%Two Way New Minor Forcing"
:: Twoay_Size_Ask="BBA doesn't support this convention"
SET Filter_Two_Notrump="%auction%2NT?"
SET Filter_Two_Over_One="%auction%1[DHS]\s+Pass\s+2[CDH]"
:: Vics_2C_Relay="BBA doesn't support this convention"
SET Filter_W2_X_XX="%auction%2(D|H|S)\s+X\s+XX"
SET Filter_We_Overcall="%auction%[1234][CDHSN]T?\s+[1234567]"
SET Filter_We_Overcall_1N="%auction%1NT?\s+[1234567]"
SET Filter_We_X_Opps_Preempt="%auction%[234][CDHS]\s+X"
SET Filter_We_X_Opps_Weak_2="%auction%2[DHS]\s+X"
SET Filter_Weak_2_Bids="%auction%2[DHS]"
SET Filter_Weak_2_Bids_Lax="%auction%2[DHS]"
SET Filter_Weak_2_Bids_Lax_Leveled="%auction%2[DHS]"
SET Filter_Weak_2_Bids_Leveled="%auction%2[DHS]"
SET Filter_Weak_Jump_Shift="1C Pass 2[DHS]|1D Pass (2[HS]|3C)|1H Pass (2S|3[CD])|1S Pass 3[CDH]"
:: Weak_NT_09-12="BBA not configured for this convention"
:: Weak_NT_09-15="BBA not configured for this convention"
:: Weak_NT_10-12="BBA not configured for this convention"
:: Weak_NT_10-13="BBA not configured for this convention"
:: Weak_NT_13-15="BBA not configured for this convention"
:: Weak_NT_14-15="BBA not configured for this convention"
:: XYZ="Unsupported by BBA?"


:AllDone