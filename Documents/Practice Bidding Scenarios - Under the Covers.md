# Practice Bidding Scenarios - Under the Covers

## BBO Deal generator

BBO includes a Deal generator that produces random hand and provides a means for constraining the deals.<br>

[CTRL-Click to check out Dealer by Hans van Staveren, et.al.](https://www.bridgebase.com/tools/dealer/dealer.php)

I've used it a little for years to generate hands for lessons I would do at a BBO Practice Table.  I would develop the dealer code and save it in a Google Document.  Then, to use it, I would open the Google Doc, copy the code, and paste it into the Dealer source/advanced and click the options I wanted.  I used this often (notice the past tense.)  

## BBOalert

During COVID, when we started playing more online bridge.  We were encouraged to alert everything.  I discovered BBOalert and created files to automate alerts in my most common partnerships.  In the fall of 2023, it occurred to me that BBOalert buttons might be used to automate the process of opening, copying, and pasting.  I approched Stanislaw Mazur, the creator of BBOalert, and asked for his help.  He gave it big time.  He continues to help.

Stanislaw figured out how to do it.  He created a JavaScript function that will load text into the Deal source at a BBO Practice Table.  It's a function call:

    setDealerCode(`text within quotes`, dealer, rotation)

where...
- text     is inclosed in `s -- it's essentially a quoted string.  For it to work, it must be valid Dealer code.
- dealer   specifies which hand is the dealer.  It should be "N", "W", "S", or "E".  "S" is the default.
- rotation specifies if the N/S hands should be randomly rotated -- True or False.  True is the default.

Following the function call, the wrapper code defines a BBOalert button which will display a short descriptive name.  When clicked will invoke the script and spit out whatever BBO Chat is included in the button.  This is all part of the JavaScript function call; so, there are restrictions about what can go in the chat.

The very last line of the button definition is what invokes the script: %theNameOfTheScript%

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

Each scenario is packaged this way.  I call it wrappered Dealer Code.  The backticks and everything outside of the ...backticks... is the wrapper.  There is a separate file for each scenario.  These are all in the pbs folder of my [CTRL-Click to check out the Practice Bidding Scenarios GitHub repository](https://github.com/ADavidBailey/Practice-Bidding-Scenarios/tree/main).  The content isn't pretty -- it evolved rather than planned.  The filenames beginning with Dealer or Gavin are wrappered Dealer code.  I've tried to use descriptive names for the scenarios.  Words are separated by Underscores, _.  Presently, the scenario files do NOT have an extension.

    

## Script files

These are Dealer code fragments that are often needed.  Stanislaw implemented an Import feature that allows me to import these snippets into other scenarios.

## Leveling

Rick Wilson introduced me to the idea of leveling and how to do it.  If for example, you want to practice Jacoby 2N, the sequences begin the same 1M - 2N then there are 5 different continuations.  1. a singleton/void, 2. a good 5-card second suit, 3. minimum semi-balanced, 4. intermediate semi-balanced, and 5. strong semi-balanced.  These do not occur with the same frequencey.  Leveling uses the presence of a small cards to reduce the probability of the most common.  For example, there's approximately a 25% chance that East holds the 2 of clubs.  So, you can define a condition, then and it with 'east has the 2C' will keep about 25% of those deals.  Check out the following two files:

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

    Import,Smolen,Import,Smolen,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/PBS/Smolen
    Import,FourthSuitForcing,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/PBS/Fourth_Suit_Forcing
    Import,Jacoby2N,https://github.com/ADavidBailey/Practice-Bidding-Scenarios/blob/main/PBS/Jacoby_2N

And, to define create and organize BBOalert buttons that cause BBOalert to invoke the i Imported the code.  Like this:

    Button,Minor/Major Sequences,,width=100% backgroundColor=lightblue
    Import,FourthSuitForcing

    Button,Notrump Sequences,,width=100% backgroundColor=lightblue
    Import,Smolen

    Button,Game Forcing Sequences,,width=100% backgroundColor=lightblue
    Import,Jacoby2N

This file contains almost 800 lines of code.  And, it imports all of the other files for a total of almost 20,000 lines of code.

BBOalert caches the url of the -PBS.txt file.  Thus, each time you start BBO, BBOalert is reloaded, and it in-turn reloads -PBS.txt which imports each and every one of the packaged dealer code files.  **Everything is up to date!**  I started BBO, just now.  18,369 records were imported.  With the BBOalert tab open, click the dark blue Data tab at the top left to see it.

## Folders in the Practice-Bidding-Scenarios GitHub repository

- PBS -- scenario files with Dealer code wrapped in code to import into BBOalert and create the buttons to load the code into BBO Practice Table Deal Source/Advanced.

Then for each file in the PBS folder, there is a corresponding file in each of these folders.

- dlr -- Dealer code striped from PBS files with Imports resolved (OneExtract.py)
- pbn -- dlr files are run through BBO's Dealer to create pbn files (makeOnePBN.cmd & oneComment.py)
- pbn-rotated-for-4-players -- pbn files are rotated for 4-handed play (makeOneRotated.cmd & BridgeComposer)
- lin-rotated-for-four-players -- rotated pbn files are converted to lin format for use with BBO (makeOneRotated.cmd & BridgeComposer)
- bba -- pbn files are run through Bridge Bidding Analyser (BBA) to add bidding (makeOneBBA.cmd, BBA.exe, and oneSummary.py)
- bba-filtered -- bba files are filtered to select only those that are bid as intended.  Note:  Rick Wilson came up with this idea.  It uses regular expressions to filter deals based on how they are bid by BBA. (filterOneScenario.cmd)
- bba-filtered-out -- bba files are NOT bid as intended (filterOneScenario.cmd)
- bidding-sheets -- this is another of Rick's ideas.  Check 'em out.  (makeOneBiddingSheet.cmd)

And a few other folders

- py -- contains Python programs
- build-scripts -- contain Windows Command File programs and Windows Power Shell programs
- Documents

The following table shows the relationship between the files in the various folders.  The folders below all have files that ard derived from and correspond to those in the PBS folder.

We've automated the process of creating all of these files derived from those in the PBS folder.  OneScriptToRuleThemAll is a Windows PowerShell program.  It accepts a scenario-name and operation-list.  Both of these parameters can have * wild-cards.  The operation-list may also have a comma-separated list of operations.  The short names for the operations are as follow"

- dlr - runs extract.py to convert PBS wrappered file(s) to a dlr file(s)
- pbn - makeOnePBN.cmd creates CMD file statement(s) to run BBO's Dealer.exe to convert a dlr file(s) to a pbn file(s)
- rotate - makeOneRotated.cmd creates CMD file statement(s) to run Bridge Composer to produce pbn-rotated... and lin-rotated... file(s)
- bba - makeOneBBA runs BBA.exe to bid hands and produces files in the bba -- a pbn with bidding added
- title - 
- filter - uses a RegEx filter to get the files that were bid as expected
- filterStats
- biddingSheet - 

There are several other folders:
- bbsa -- Convention Cards for Bridge Bidding Analyser.  There's a 21GF-DEFAULT that's used for most scenarios.  For scenarios that need something different, I try to copy the DEFAULT and make the necessary changes.  I try to NOT change the DEFAULT.
- build-scripts -- Windows CMD and Powershell Programs.  In some cases, these invoke code: Dealer.exe, BBA.exe, and BridgeComposer.exe
- Documents -- Documentation for the Practice-Bidding-Scenarios GitHub repository.
- lin -- a lin files for BBO Practice Table.  It just has one mixed.lin file, today.
- misc -- everything has to go somewhere
- py -- Python programs
- script -- BBO Dealer code fragments that may be Imported into PBS files -- be careful modifying these as they may break any scenario that imports them.



Since we have all of these scenarios, We wanted to leverage them.  I've created python programs that use the dlr files to create pbn, rotated pbn, and rotated lin files that can be used elsewhere.  When scenarios are updated or new scenarios are created, the following programs are in the py folder of the PBS root directory and are used to create/update the pbn and lin files.



## Acknowledgements

I've had a lot of help with this project.

*Stanislaw Mazur*, the creator of BBOalert.  When I first realized the the BBOalert buttons might load the Dealer, I approached Stanislaw.  This could not have been without his help, and lots of it.

*Matthew Kidd*, the creator of BBO Helper, helped me write a decent description of my project and to get it posted on Bridge Winners.

*Bob Wesneski*, a long-time friend and fellow programmer (15 years younger and, thus, knew some current programming languages), helped me with a proof of concept project to create lin files from the Dealer code I had developed.  I think he'll be pleased to know that we're about there.

*Gavin Wolpert*, a professional bridge player and teacher, needs no introduction.  Just as I got this working Gavin joined me in a short Zoom where I showed him what I was working on.  His enthusiastic response boosted my energy level and propeled the project further.  I've implemented Scenarios to support several of his classes.  He's given me access to several of his Lessons and I've created Scenarios for them.  I'm looking forward to more.

*Rick Wilson*, called me and said, I think we're working on the same thing -- using BBO Dealer to generate hands for practice.  He's been an inspiration for generating the pbn and lin files.  And helping me to get started with Parallels, Windows, Bridge Composer, Bidding Analyser.

*Thorvald Aagaard* began using my code to create deals for training Ben.  He's discovered many bugs for me to fix.  Since I've begun working with pbn and lin files, Thorvald has been a mentor an coach.

*Edward Piwowar*'s, Bridge Bidding Analyser, has been a big help as we have progressed from the BBO Practice Table to creating pbn and lin files.  BBA enables us to see how the deals are bid and what conventions are used.  I use this information to adjust the deal constraints and to filter the bid deals.

*Ray Spalding*'s, Bridge Composer has great features for manipulating bridge files.  Ray has helped us create and use JavaScript filters.

*Bob Richardson*'s, Double Dummy Solver, helps assess the Bridge Bidding Analyser's bidding. 


## Regrets

If I had a do-over
 - I'd give all of my wappered files a common extension, maybe .pbs
 
