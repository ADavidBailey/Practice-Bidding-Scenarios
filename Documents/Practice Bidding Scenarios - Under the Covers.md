# Practice Bidding Scenarios - Under the Covers

## BBO Deal generator

BBO includes a Deal generator -- Dealer by Hans van Staveren, et.al.  It's accessible on the BBO site.
    
    https://www.bridgebase.com/tools/dealer/dealer.php

I've used it a little for years to generate hands for lessons I would do at a BBO Practice Table.  I would develop the dealer code and save it in a Google Document.  Then, to use it, I would open the file, copy the code, and paste it into the Dealer source/advanced.  I used this often.

## BBOalert

During COVID, when we started playing more online bridge.  We were encouraged to alert everything.  I discovered BBOalert and created files to automate alerts in my most common partnerships.  Last fall, it occurred to me that BBOalert buttons might be used to automate the process of opening, copying, and pasting.  I approched Stanislaw Mazur, the creator of BBOalert, and asked for his help.  He gave it big time.  He continues to help.

Stanislaw figured out how to do it.  He created a function that will load text into the Deal source at a BBO Practice Table.  It's a function call:

    setDealerCode(`text`, dealer, rotation)

where...
- text     is inclosed in `s -- it's essentially a quoted string.  For it to work, it must be valid Dealer code.
- dealer   specifies which hand is the dealer.  It should be "N", "W", "S", or "E".  "S" is the default.
- rotation specifies if the N/S hands should be randomly rotated.  The value True or False.  True is the default.

Script,theNameOfTheScript<br>
setDealerCode(`dealer code string`,dealer,rotation)

Following the function call, the wrapper code defines a BBOalert button which will display a short descriptive name and when clicked will invoke the script.  Imbeded in the Button definition, is text to be displayed in the BBO chat.

The very last line of the button is what invokes the script: %theNameOfTheScript%

Note: some of the scenarios have hundreds of lines of Dealer code.

Each scenario is packaged this way.  I call it wrappered Dealer Code.  The ` ` and everything outside of the ...` `... is the wrapper.  There is a separate file for each scenario.  These are all in the root directory of my Practice Bidding Scenarios GitHub repository.  It ain't pretty.  The filenames beginning with Basic, Dealer, and Gavin are wrappered Dealer code.  And, I apologize for the awful names with spaces and special characters.

    https://github.com/ADavidBailey/Practice-Bidding-Scenarios/tree/main

## -Script files

These are code snippits that are often needed.  Stanislaw implemented an Include feature that allows me to include these snippets in other scenarios.

## Leveling

Rick Wilson introduced me to the idea of leveling and how to do it.  If for example, you want to practice Jacoby 2N, the sequences begin the same 1M - 2N then there are 5 different continuations.  1. a singleton/void, 2. a good 5-card second suit, 3. weak semi-balanced, 4. intermediate semi-balanced, and 5. strong semibalanced.  These do not occur with the same frequencey.  Leveling uses the presence of a small card to reduce the probability of the most common.  There's approximately a 25% chance that east holds the 2 of clubs.  So, you can code something do it and (hasShortness and east has the 2C) will keep about 25% of those deals.  Check out the following two files:

    https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/-Script-Leveling
    https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/-Example%20Leveling


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

BBOalert caches the url of the -PBS.txt file.  Thus, each time you start BBO, BBOalert is reloaded, and it in-turn reloads -PBS.txt and each and every one of the packaged dealer code files.  Everything is up to date.  I started BBO, just now.  13,599 records were loaded.

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

<mark>dealer</mark> is the dealer.exe file which reades each .dlr file and writes corresponding .pbn file.  The -s= is a random number seed.  If my code is the same and the seed is the same, it will produce the same hands each time it's run.  When I want new file, I can pick a different seed.  Here's the way to use it.

    python3 adbMakePBN.ph > run.cmd

And, then go to Window's Command Prompt and enter:

    run.cmd

this one runs a while (currently about 30 minutes for 179 scenarios).  It prints out the name of each file so you can see what's happening.

### adbCommentStats.py

Most of the pbn files include some statistics.  They are ignored by BBO; but, some other programs don't like them.  So, this program converts them into comment lines that are part of the pbn standard -- lines beginning with a # are ignored.  This program changes all of the statistics to comments by adding a # and a space to the beginning of the line.  It also prints out the statistics for all of the files. Run it like this to create stats.txt:

    python3 adbCommentStats.py > stats.txt

Or, just look here:

    https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/stats.txt

### adbRotate.py

This program reads all of files in the pbn folder and creates corresponding files in the pbn-rotated-for-4-players.  Rotates the deals in pbn files so they're suitable for four-hand play.

### adbPBNtoLin.py

This program reads all files in the pbn-rotated-for-4-players folder and creates corresponding files in the lin-rotated-for-four-players folder.  These have the extension .lin

## Acknowledgements

I've had a lot of help with this project.

*Stanislaw Mazur*, the creator of BBOalert.  When I first realized the the BBOalert buttons might load the Dealer, I approached Stanislaw.  This could not have been without his help, and lots of it.

*Matthew Kidd*, the creator of BBO Helper, helped me write a decent description of my project and to get it posted on Bridge Winners.

*Bob Wesneski*, a long-time friend and fellow programmer (15 years younger and thus, knew some current programming languages), helped me with a proof of concept project to create lin files from the Dealer code I had developed.  I think he'll be pleased to know that we're about there.

*Gavin Wolpert* needs no introduction.  Just as I got this working Gavin joined me in a short Zoom where I showed him what I was working on.  His enthusiastic response boosted my energy level and propeled the project further.  I've implemented Scenarios to support several of his classes.  He's given me access to several of his Lessons and I've created Scenarios for them.

*Rick Wilson*, called me and said, I think we're working on the same thing -- using BBO Dealer to generate hands for practice.  He's been an inspiration for generating the pbn and lin files.  And helping me to get started with Parallels, Windows, Bridge Composer, Bidding Analyser.

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
