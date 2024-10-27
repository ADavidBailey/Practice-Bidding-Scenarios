param (
    [string]$WildCardScenarioSpec,
    [string]$Operation
)

# Function to perform actions on the file
function Perform-Actions {
    param (
        [string]$File
    )
    echo "Performing actions on $File"
    Perform-Action -Operation "extract" -File $File
    Perform-Action -Operation "makePBN" -File $File
    Perform-Action -Operation "commentStats" -File $File
    Perform-Action -Operation "rotate" -File $File
    Perform-Action -Operation "makeBBA" -File $File
    Perform-Action -Operation "bbaSummary" -File $File
    Perform-Action -Operation "makeFiltered" -File $File
    Perform-Action -Operation "makeBiddingSheet" -File $File
}

# Function to perform a specific action on the file
function Perform-Action {
    param (
        [string]$Operation,
        [string]$File
    )

    $Scenario = Split-Path -Path $File -Leaf

    switch ($Operation) {
        "extract" {
            echo "Extracting $Scnario from PBS to dlr"
            & P:\python3 extract.py $Scenario
        }
        "makePBN" {
            echo "Generating PBN for $Scenario"
            & P:\build-scripts\makeOnePBN.cmd $Scenario
        }
        "commentStats" {
            echo "Change Stats to comments for $Scenario"
            #Move-Item -Path $File -Destination $movedFile
        }
        "rotate" {
            echo "Rotating PBN for $Scenario to pbn-rotated-for-4-players and lin-rotated-for-4-players"
            & P:\build-scripts $Scenario
        }
        "makeBBA" {
            echo "Generating BBA for $Scenario"
            & P:\build-scripts\makeOneBBA.cmd $Scenario
        }
        "bbaSummary" {
            echo "Summarizing BBA for $Scenario"
            & P:\build-scripts\wBbaSummary.py $Scenario
        }
        "makeFiltered" {
            echo "Generating filtered and filtered-out for $Scenario"
            & P:\build-scripts\makeOneFiltered $Scenario
        }
        "makeBiddingSheet" {
            echo "Generating bidding sheet for $Scenario"
            & P:\build-scripts\makeOneBiddingSheet.cmd $Scenario
        }
        default {
            echo "Unknown operation: $Operation"
        }
    }
}

# Main script execution
if (-not $WildcardScenarioSpec -or -not $Operation) {
    echo "Usage: .\file_operations.ps1 [wildcard_file_specification] [operation]"
    exit 1
}

# Get files matching the wildcard specification
$files = Get-ChildItem -Path p:\pbs -Recurse -File | Where-Object { $_.Name -like $WildcardScenarioSpec }

foreach ($file in $files) {
    echo "Processing file: $file"
    if ($Operation -eq "*") {
        Perform-Actions -File $file.FullName
    } else {
        Perform-Action -Operation $Operation -File $file.FullName
    }
}
