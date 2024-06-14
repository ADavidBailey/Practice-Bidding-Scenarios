# Practice Bidding Scenarios - Under the Covers

## -PBS.txt

This is the file that is pasted into BBOalert.  It contains some code pecular to Practice Bidding Scenarios.  For example, code to Start Bidding/Teaching tables, to Open Deal source, to display HCP at the top of the screen.  Most of the code Import Definitions, the various scenario files with statements like this:

    Import,Smolen,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/Dealer%20Smolen.txt
    Import,FourthSuitForcing,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/Dealer%20FourthSuitForcing
    Import,Jacoby2N,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/Dealer%20Jacoby%202N.txt

And, to define create and organize BBOalert buttons that cause BBOalert to invoke the i Imported the code.  Like this:

    Button,Minor/Major Sequences,,width=100% backgroundColor=lightblue
    Import,FourthSuitForcing

    Button,Notrump Sequences,,width=100% backgroundColor=lightblue
    Import,Smolen

    Button,Game Forcing Sequences,,width=100% backgroundColor=lightblue
    Import,Jacoby2N

This file contains almost a thousand lines of code.

The imported scenario files consist of two parts.  <mark>Wrapper code</mark> (highlighted) to invoke a script to load the dealer code into the BBO Deal source and display chat, and to invoke the script to load the dealer code in the BBO Deal source all surrounding the dealer code itself:

## The Wrappered Dealer code

<mark>It starts with the invocation of a script...</mark>

    Script,theNameOfThisScript
    setDealerCode(`

<mark>The first parameter to the script is the Dealer. It is enclosed in back-ticks...</mark>

    
    The Dealer code is very, very long, multi-line string to be loaded into
    the 'Dealer source' on a BBO Bidding or Teaching table.  This
    dealer code is read and used by BBO's Dealer by Hans van Staveren, et.al.

        https://www.bridgebase.com/tools/dealer/dealer.php

    The string is delinieated by back tics.  The string may include 'Import' that 
    bring in common reusable snippets of dealer code.  Here's an example:

        Import,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/-Script-Predict-Opening-1-Bid
    
    This long string is followed the rest of the wrapper.
        - dealer has a value of "N", "E", "S", or "W", if not specified, it
        defaults to "S"
        - rotate has a value of True or False.  The default is True.
        - the BBOalert button definition
        - the chat
        - the name of the script to be executed -- a reference to the name of this very script
    
<mark>At the end of the Dealer code we specify the 2nd and 3rd parameters to the script -- the dealer and rotation...</mark>

    `,"N",true),
    Script,

<mark>Then we define the BBOalert button...</mark>

    Button,short name,

<mark>The BBO chat...
    --- Descriptive name for scenario
    Chat to be spit out when the BBOalert
    button is clicked and string is loaded
    into 'Dealer source' at a BBO practice table.

<mark>We invoke the script -- the script that we just defined...</mark>

    %theNameOfThisScript%

<mark>And, finally, the end of the wrapper code.  Everything except the Dealer code is the wrapper.</mark>

The total lines of code -- the -PBS.txt and the imported wrappered Dealer code is approaching 14,000 lines of code.

## Special Programs for pbn and lin files

When scenarios are updated or new scenarios are created, you need to update the pbn and lin files.

### adbExtract.py

This program reads in Practice Bidding Scenarios.  For each filename that starts with Basic, Dealer, or Gavin, it extracts the Dealer Code from the BBOalert wrapper -- that's the very, very log string.  It processes any 'Imports' and creates dlr files that corresponding to each of the scenarios.  Spaces and special characters in filenames are translated to characters that are valid in filenames (space to -).  The .dlr files are suitable to be processed directly by BBO Dealer: 

    https://www.bridgebase.com/tools/dealer/dealer.php

Try some.  

If you have access to these files in you own Practice Bidding Scenarios folder and enter:

    python3 adbExtract.py

### adbMakePBN.py

This program reads the files in the dlr folder and creates Windows commands that will create corresponding pbn files.  These commands are put into DOS command file run.cmd  Each record in the run.cmd looks like this:

    P:\dealer</mark> P:\dlr\Dealer-3N-over-LHO-3x-W.dlr -s=675264029 >P:\pbn\Dealer-3N-over-LHO-3x-W.pbn

<mark>dealer</mark> is the dealer.exe file which reades each .dlr file and writes corresponding .pbn file.  Look up 'Dealer by Hans van Staveren and others'.

    python3 adbMakePBN.ph > run.cmd

then go to Window's Command Prompt and enter:

    run.cmd

this one runs a while (currently about 30 minutes).  It prints out the name of each file so you can along.

### adbCommentStats.py
Most of the pbn files include some statistics.  They are ignored by BBO; but, some other programs don't like them.  So, this program converts them into comment lines that are part of the pbn standard.  Lines beginning with a # are ignored.  This program changes all of the statistics to comments by adding a # and a space to the beginning of the line.  It also prints out the statistics for all of the files. Run it like this to create stats.txt:

    python3 adbCommentStats.py > stats.txt

### adbRotate.py

This program reads all of files in the pbn folder and creates corresponding files in the pbn-rotated-for-4-players.  Rotates the deals in pbn files so they're suitable for four-hand play.

### adbPBNtoLin.py

This program reads all files in the pbn-rotated-for-4-players folder and creates corresponding files in the lin-rotated-for-four-players folder.  These have the extension .lin

## Regrets

If I had a do-over
 - I'd git rid of the .txt extension on the PBS.txt file
 - I'd give all of my wappered files a common extension, maybe .pbs
 - I'd put them all in a bbo folder
 - I'd get rid of the Basic, Dealer, Gavin prefixes to the names
 - I'd get rid of spaces & special characters in filenames
 - I'd put my adbxxx.py files in a py folder
 
 To fix this at this point, I'd have to write another .py to make the changes.
