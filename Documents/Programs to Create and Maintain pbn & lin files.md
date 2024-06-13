# Code to create and maintain Practice Bidding Scenarios and related pbn & lin files

## -PBS.txt

This is the file that is pasted into BBOalert.  It contains some code pecular to Practice Bidding Scenarios.  For example, code to Start Bidding/Teaching tables, to Open Deal source, to display HCP at the top of the screen.  Most of the code Imports, the various scenario files with statements like this:

    Import,Smolen,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/Dealer%20Smolen.txt
    Import,FourthSuitForcing,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/Dealer%20FourthSuitForcing
    Import,Jacoby2N,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/Dealer%20Jacoby%202N.txt

And, to define create and organize BBOalert buttons that will load the code.  Like this:

    Button,Minor/Major Sequences,,width=100% backgroundColor=lightblue
    Import,FourthSuitForcing

    Button,Notrump Sequences,,width=100% backgroundColor=lightblue
    Import,Smolen

    Button,Game Forcing Sequences,,width=100% backgroundColor=lightblue
    Import,Jacoby2N


The scenario files consist of two parts,

    setDealerCode(<script-name>,`

    A very, very long, multi-line string of dealer code to be loaded into
    the 'Dealer source' on a BBO Bidding or Teaching table.  This
    dealer code is read and used by BBO's Dealer by Hans van Staveren, et.al.

    The string is delinieated by back tics.  The string may include 'Import' that 
    bring in common reusable snippets of dealer code.  Here's an example:

        Import,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/-Script-Predict-Opening-1-Bid
    
    This long string is followed by two additional parameters.
        - dealer has a value of "N", "E", "S", or "W", if not specified, it
          defaults to "S"
        - rotate has a value of True or False.  The default is True.

    `,<dealer>,<rotate>),
    Chat to be spit out when the BBOalert\n
    button is clicked and string is loaded\n
    into 'Dealer source' at a BBO practice table.\n
    %<script-name>%

## adbExtract
This program reads in Practice Bidding Scenarios.  For each filename that starts with Basic, Dealer, or Gavin, it extracts the Dealer Code from the BBOalert wrapper -- that's the very, very log string.  It processes any 'Imports' and puts the saves the code to the dlr folder with a .dlr extension.  Spaces are removed from filenames and replaced with -'s.