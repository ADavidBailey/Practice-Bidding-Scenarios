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

The imported scenario files consist of two parts.  Wrapper code to define a script which will load the dealer code into the BBO Deal source, to create a BBOalert button which displays a short name of the script and when clicked, will invoke the script.  The first parameter to the script is the actual Dealer code -- it's very long with many, many lines.

## The Wrappered Dealer code

Stanislaw Mazur created a function that will load text into the Deal source at a BBO Practice Table.  It's a function call:

setDealerCode(`text`, dealer, rotation)

- text     is inclosed in `s -- it's essentially a quoted string.  For it to work, it must be valid Dealer code.
- dealer   specifies which hand is the dealer.  It should be "N", "W", "S", or "E".  "S" is the default.
- rotation specifies if the N/S hands should be randomly rotated.  The value True or False.  True is the default.

Script,theNameOfTheScript setDealerCode(`dealer code string`,dealer,rotation)

Following the function call, the wrapper code defines a BBOalert button which will display a short descriptive name and when clicked will invoke the script.  Imbeded in the Button definition, is text to be displayed in the BBO chat.

The very last line of the button is what invokes the script: %theNameOfTheScript%

The total lines of code in -PBS.txt and the imported wrappered Dealer code is approaching 14,000 lines.

## Special Programs for pbn and lin files

When scenarios are updated or new scenarios are created, we need to update the pbn and lin files.

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

And, then go to Window's Command Prompt and enter:

    run.cmd

this one runs a while (currently about 30 minutes).  It prints out the name of each file so you can along.

### adbCommentStats.py

Most of the pbn files include some statistics.  They are ignored by BBO; but, some other programs don't like them.  So, this program converts them into comment lines that are part of the pbn standard.  Lines beginning with a # are ignored.  This program changes all of the statistics to comments by adding a # and a space to the beginning of the line.  It also prints out the statistics for all of the files. Run it like this to create stats.txt:

    python3 adbCommentStats.py > stats.txt

### adbRotate.py

This program reads all of files in the pbn folder and creates corresponding files in the pbn-rotated-for-4-players.  Rotates the deals in pbn files so they're suitable for four-hand play.

### adbPBNtoLin.py

This program reads all files in the pbn-rotated-for-4-players folder and creates corresponding files in the lin-rotated-for-four-players folder.  These have the extension .lin

## Acknowledgements

I've had a lot of help with this project.

*Stanislaw Mazur*, the creator of BBOalert.  When I first realized the the BBOalert buttons might load the Dealer, I approached Stanislaw.  This could not have been without his help, and lots of it.

*Matthew Kidd*, the creator of BBO Helper, helped me write a decent description of my project and to get it posted on Bridge Winners.

*Bob Wesneski*, a long-time friend and fellow programmer (15 years younger), helped me with a proof of concept project to create lin files from the Dealer code I had developed.  I think he'll be pleased to know that we're about there.

*Gavin Wolpert* needs no introduction.  Just as I got this working Gavin joined me in a short Zoom.  His enthusiastic response boosted my energy level and propeled the project further.  I've implemented Scenarios to support several of his classes.  He's given me access to several of his Lessons and I've created Scenarios for them.

*Rick Wilson*, called me and said, I think we're working on the same thing -- using BBO Dealer to generate hands for practice.

*Thorsvald Aagaard* began using my code to create deals for training Ben.  He's discovered many bugs for me to fix.  Since I've begun working with pbn and lin files, Thorvald has been a mentor an coach.


## Regrets

If I had a do-over
 - I'd git rid of the .txt extension on the PBS.txt file
 - I'd give all of my wappered files a common extension, maybe .pbs
 - I'd put them all in a bbo folder
 - I'd get rid of the Basic, Dealer, Gavin prefixes to the names
 - I'd get rid of spaces & special characters in filenames
 - I'd put my adbxxx.py files in a py folder
 
 To fix this at this point, I'd have to write another .py to make the changes.
