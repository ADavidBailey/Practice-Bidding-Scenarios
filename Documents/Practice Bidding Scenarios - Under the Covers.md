# Practice Bidding Scenarios - Under the Covers

## BBO Deal generator

BBO includes a Deal generator that produces random hand and provides a means for constraining the deals.<br>

[CTRL-Click to check out Dealer by Hans van Staveren, et.al.](https://www.bridgebase.com/tools/dealer/dealer.php)

I've used it a little for years to generate hands for lessons I would do at a BBO Practice Table.  I would develop the dealer code and save it in a Google Document.  Then, to use it, I would open the Google Doc, copy the code, and paste it into the Dealer source/advanced and click the options I wanted.  I used this often (notice the past tense.)  

## BBOalert

During COVID, when we started playing more online bridge.  We were encouraged to alert everything.  I discovered BBOalert and created files to automate alerts in my most common partnerships.  Last fall, it occurred to me that BBOalert buttons might be used to automate the process of opening, copying, and pasting.  I approched Stanislaw Mazur, the creator of BBOalert, and asked for his help.  He gave it big time.  He continues to help.

Stanislaw figured out how to do it.  He created a function that will load text into the Deal source at a BBO Practice Table.  It's a function call:

    setDealerCode(`text within quotes`, dealer, rotation)

where...
- text     is inclosed in `s -- it's essentially a quoted string.  For it to work, it must be valid Dealer code.
- dealer   specifies which hand is the dealer.  It should be "N", "W", "S", or "E".  "S" is the default.
- rotation specifies if the N/S hands should be randomly rotated -- True or False.  True is the default.

Following the function call, the wrapper code defines a BBOalert button which will display a short descriptive name and when clicked will invoke the script.  Imbeded in the Button definition, is text to be displayed in the BBO chat.

The very last line of the button is what invokes the script: %theNameOfTheScript%

The whole thing looks like this:

    Script,theNameOfTheScript<br>
    setDealerCode(`<br>

    dealer code string<br>
    many, many lines of Dealer code.<br>

    Some scenarios have hundrends of lines.  The average is under 100 lines.<br>

    `,dealer,rotation)<br>
    Script<br>
    Button,Short Name,<br>
    --- Long Descriptive Name<br>
    Descriptive lines<br>
    More deacriptive lines<br>
    %theNameOfTheScript%<br>

Each scenario is packaged this way.  I call it wrappered Dealer Code.  The backticks and everything outside of the ...backticks... is the wrapper.  There is a separate file for each scenario.  These are all in the root directory of my [CTRL-Click to check out the Practice Bidding Scenarios GitHub repository](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/tree/main).  For brevity, I'll use the acronym, PBS, for the root directory.  The content isn't pretty -- it evolved rather than planned.  The filenames beginning with Dealer or Gavin are wrappered Dealer code.  And, I apologize for the awful names with spaces and special characters.

    

## Script files

These are code fragments that are often needed.  Stanislaw implemented an Import feature that allows me to include these snippets in other scenarios.

## Leveling

Rick Wilson introduced me to the idea of leveling and how to do it.  If for example, you want to practice Jacoby 2N, the sequences begin the same 1M - 2N then there are 5 different continuations.  1. a singleton/void, 2. a good 5-card second suit, 3. minimum semi-balanced, 4. intermediate semi-balanced, and 5. strong semi-balanced.  These do not occur with the same frequencey.  Leveling uses the presence of a small cards to reduce the probability of the most common.  There's approximately a 25% chance that east holds the 2 of clubs.  So, you can code something do it and (hasShortness and east has the 2C) will keep about 25% of those deals.  Check out the following two files:

[CTRL-Click -Script-Leveling](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/-Script-Leveling)<br>
[CTRL-Click for Leveling Example](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/-Example%20Leveling)

## -PBS.txt

This is the file that is pasted into BBOalert.  It contains some code specific to Practice Bidding Scenarios.  For example, it includes code for the following:

- Start Bidding/Teaching tables
- Open Deal source
- Display HCP at the top of the screen.  
- Redirects BBO chat to go to you, the user.  This avoids my chat going to the lobby
- Expand/collapse sections in the Practice Bidding Scenarios Shortcuts

Most of the code is Import Definitions for the various scenario files with statements like this:

    Import,Smolen,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/PBS/Smolen
    Import,FourthSuitForcing,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/PBS/Fourth_Suit_Forcing
    Import,Jacoby2N,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/PBS/Jacoby_2N

And, to define create and organize BBOalert buttons that cause BBOalert to invoke the i Imported the code.  Like this:

    Button,Minor/Major Sequences,,width=100% backgroundColor=lightblue
    Import,FourthSuitForcing

    Button,Notrump Sequences,,width=100% backgroundColor=lightblue
    Import,Smolen

    Button,Game Forcing Sequences,,width=100% backgroundColor=lightblue
    Import,Jacoby2N

This file contains almost 800 lines of code.

BBOalert caches the url of the -PBS.txt file.  Thus, each time you start BBO, BBOalert is reloaded, and it in-turn reloads -PBS.txt and each and every one of the packaged dealer code files.  Everything is up to date.  I started BBO, just now.  14,127 records were imported.  With the BBOalert tab open, click the dark blue Data tab at the top left to see it.

## Folders in the Practice-Bidding-Scenarios GitHub repository

1. PBS -- scenario files with Dealer code wrapped in code to import into BBOalert and create the buttons to load the code into BBO Practice Table Deal Source/Advanced.
2. dlr -- Dealer code striped from PBS files with Imports resolved
3. pbn -- dlr files are run through BBO's Dealer to create pbn files
4. pbn-rotated-for-4-players -- pbn files are rotated for 4-handed play
5. lin -- pbn files are converted to lin format for use with BBO
6. lin-rotated-for-four-players -- rotated pbn files are converted to lin format for use with BBO
7. bba -- pbn files are run through Bridge Bidding Analyser to add bidding
8. bba-filtered -- bba files are filtered to select only those that are bid as intended
9. bba-filtered-out -- bba files are NOT bid as intended

The following table shows the relationship between the files in the various folders.  The folders below all have files that correspond to those in the PBS folder.

| Program | from | to |
| -------------------- | ------------------------------ | ------------------------------------ |
| extract.py   |  PBN | dlr |
| makePBN.py | dlr | makePBN.cmd
| makePBN.cmd | dlr | pbn |
| commentStats.py | pbn | pbn |
| rotate.py | pbn | pbn-rotated-for-4-players |
| PBNtoLIN.py. | pbn-rotated-for-4-players | lin-rotated-for-4-players |
| makeBBA.py | pbn | makeBBA.cmd |
| makeBBA.cmd | pbn | bba |
| bbaSummary.py | bba | bba-summary |
| makeFiltered.cmd  | bba | bba-filtered

Other folders:
- bbsa -- Bridge Bidding Analyser Convention Cards
- build-scripts -- Windows CMD Programs to run BBA and Dealer
- Documents -- Documentatio for the Practice-Bidding-Scenarios GitHub repository
- misc
- py -- Python programs (see below)
- script -- BBO Dealer code fragments that are Imported into PBS files
- TESTING


## Special Programs for pbn and lin files

Since we have all of these scenarios, I wanted to leverage them.  I've created python programs that use the dlr files to create pbn, rotated pbn, and rotated lin files that can be used elsewhere.  When scenarios are updated or new scenarios are created, the following programs are in the py folder of the PBS root directory and are used to create/update the pbn and lin files.

### extract.py

This program reads all of through all of the files in the PBS folder -- one for each scenario.  For each file, it extracts the Dealer Code from the BBOalert wrapper, it processes any 'Imports', and creates dlr files that corresponding to each of the scenarios.  The dlr files are suitable to be processed directly by BBO Dealer which is linked above.  Switch to the py folder and enter the following

    python3 extract.py

[CTRL-Click here to see the dlr files](<https://github.com/ADavidBailey/Practice-Bidding-Scenarios/tree/main/dlr>)

### makePBN.py

This program reads the files in the dlr folder and creates Windows commands that will create corresponding pbn files.  These commands are put into DOS command file 'makePBN.cmd' which resides in the PBS root directory.  To run this, switch to the py folder and enter the following.

    python3 makePBN.py

Here's an example of a record the makePBN.cmd:

    P:\dealer P:\dlr\Dealer-3N-over-LHO-3x-W.dlr -s=675264029 >P:\pbn\Dealer-3N-over-LHO-3x-W.pbn

The first P:\dealer invokes the dealer.exe with 3 parameters, 1. the file to read and 2.the seed.  The > directs the output to the corresponding pbn file.

If my code is the same and the seed is the same, it will produce the same hands each time it's run.  The seed is derived from the filename.  If/When I want to produce new files, I can change the seed.

[CTRL-Click here to see makePBN.cmd](<https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/makePBN.cmd>)

And, then go to Window's Command Prompt, switch to the PBS root directory and enter:

    makePBN.cmd

this one runs a while (currently about 1 hour and 25 minutes for 179 scenarios).  It prints out the name of each file so you can see what's happening.

### commentStats.py

Most of the pbn files include some statistics.  They are ignored by BBO; but, some other programs don't like them.  So, this program converts them into comment lines that are part of the pbn standard -- lines beginning with a % are ignored.  This program changes all of the statistics to comments by adding a % and a space to the beginning of the line.  It also prints out the statistics for all of the files and puts the results in stats.txt.  Switch to the py directory and enter the following to create the stats.txt file in the PBS root directory:

    python3 commentStats.py

[CTRL-Click here to see stats.txt](<https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/stats.txt>)

### rotate.py

This program reads all of files in the pbn folder and creates corresponding files in the pbn-rotated-for-4-players.

The Scenarios are designed for use at a BBO Practice Table.  They are designed for the user to sit in the South seat.  So a scenario intended to help a user know what to open, South will be the dealer.  If that deal is put in Board 1 of a file, it needs to be rotated so that North is the dealer.  Other scenarios might require that West is the opener.  For example, if the intent is to practice jump overcalls, we need for West to be the dealer.

When we put the deals into pbn and lin files intended for 4 people to play, they need to be rotated so that the intended dealer is in the seat of the board number -- board 1 is North, 2 is West, 3 is South, and 4 is North...

This code reads all of the files in the pbn folder and writes corresponding files to the pbn-rotated-for-4-players folder.  It appends a -R to the filename.

Switch to the py folder and enter the following:

    python3 rotate.py

### PBNtoLIN.py

This program reads all files in the pbn-rotated-for-4-players folder and creates corresponding files in the lin-rotated-for-four-players folder.  These have the extension '.lin'.  Switch to the py folder and enter the following:

    python3 PBNtoLIN.py

### makeBBA.py

This program reads all .pbn files from the /pbn folder and creates a DOS command file for running BBA.exe. The BBA archive file is created in the /bba directory.  It's in .pbn format.

Switch to the py folder and enter the following:

    python3 makeBBA.py

This will create makeBBA.cmd.  **CAUTION** -- read the rest of this.
          
The code appends to the archive file if it already exists; so, we need to delete the existing file.  makeBBA.cmd has two DOS commands for each scenario.  One is to delete the existing archive file, and the other to create a new one.

The normal use case is to update the bba files for a few scenarios -- Open makeBBA.cmd in a text editor, select the ones you want to update and copy/paste the code to a DOS command prompt OR to a small updateBBA.cmd file.

These pbn files are large.  Creating/updating all of these files at once will cause an issue with GitHub.  I recommend doing about 50 at a time -- copy/paste 50, run updateBBA.cmd, sync 50, and repeat.

### bbaSummary.py

This program reads all of the files from the bba folder and creates corresponding files with three different summaries:

    1. a one-line record of each deal, showing the hands, auctions, notes, and more.
    2. a sorted summary of the auctions
    3. a sorted summary of the BBA 'notes' (alerts)

This file is in .txt format.

### mix4.py

This program creates a mixed 16-deal set of boards -- 4 boards from each of 4 scenarios.  This example has boards from Drury, Smolen, FourthSuitForcing, and Jacoby-2N.  It's in .lin format; so, you can import it into your BBO/Account/Deal archive.  Then, you can use it at a Bidding/Teaching Table -- Deal source/Use saved deals.

The program picks a random starting point; so, each time it's run you should get a different set of deals.

[CTRL-Click here to see -mixed.lin](<https://tinyurl.com/MixedLin>)

I'm still working on a UI where users can create their own mixed deal set.

## Acknowledgements

I've had a lot of help with this project.

*Stanislaw Mazur*, the creator of BBOalert.  When I first realized the the BBOalert buttons might load the Dealer, I approached Stanislaw.  This could not have been without his help, and lots of it.

*Matthew Kidd*, the creator of BBO Helper, helped me write a decent description of my project and to get it posted on Bridge Winners.

*Bob Wesneski*, a long-time friend and fellow programmer (15 years younger and thus, knew some current programming languages), helped me with a proof of concept project to create lin files from the Dealer code I had developed.  I think he'll be pleased to know that we're about there.

*Gavin Wolpert*, a professional bridge player and teacher, needs no introduction.  Just as I got this working Gavin joined me in a short Zoom where I showed him what I was working on.  His enthusiastic response boosted my energy level and propeled the project further.  I've implemented Scenarios to support several of his classes.  He's given me access to several of his Lessons and I've created Scenarios for them.  I'm looking forward to more.

*Rick Wilson*, called me and said, I think we're working on the same thing -- using BBO Dealer to generate hands for practice.  He's been an inspiration for generating the pbn and lin files.  And helping me to get started with Parallels, Windows, Bridge Composer, Bidding Analyser.

*Thorvald Aagaard* began using my code to create deals for training Ben.  He's discovered many bugs for me to fix.  Since I've begun working with pbn and lin files, Thorvald has been a mentor an coach.

*Edward Piwowar*'s, Bridge Bidding Analyser, has been a big help as I have progressed from the BBO Practice Table to creating pbn and lin files.  BBA enables me to see how the deals are bid and what conventions are used.  I use this information to adjust the deal constraints.

*Bob Richardson*'s, Double Dummy Solver, helps me assess the Bridge Bidding Analyser's bidding. 


## Regrets

If I had a do-over
 - I'd get rid of the .txt extension on the PBS.txt file
 - I'd give all of my wappered files a common extension, maybe .pbs
 
