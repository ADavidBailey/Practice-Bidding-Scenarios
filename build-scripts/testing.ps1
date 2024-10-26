param (
    [string]$WildcardFileSpec,
    [string]$Operation
)

# Function to perform actions on the file
function Perform-Actions {
    param (
        [string]$File
    )
    Write-Host "Performing actions on $File"
    Perform-Action -Operation "extract" -File $File
    Perform-Action -Operation "makePBN" -File $File
    Perform-Action -Operation "commentStats" -File $File
    Perform-Action -Operation "makeBBA" -File $File
    Perform-Action -Operation "bbaSummary" -File $File
    Perform-Action -Operation "filter" -File $File
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
            $backupFile = "$File.bak"
            Write-Host "Extracting $File to dlr"
            #Copy-Item -Path $File -Destination $backupFile
        }
        "makePBN" {
            Write-Host "Generating PBN for $Scenario"
            & P:\build-scripts\makeOnePBN.cmd $Scenario
        }
        "commentStats" {
            $movedFile = "$File.moved"
            Write-Host "Change Stats to comments for $File"
            #Move-Item -Path $File -Destination $movedFile
        }
        default {
            Write-Host "Unknown operation: $Operation"
        }
    }
}

# Main script execution
if (-not $WildcardFileSpec -or -not $Operation) {
    Write-Host "Usage: .\file_operations.ps1 [wildcard_file_specification] [operation]"
    exit 1
}

# Get files matching the wildcard specification
$files = Get-ChildItem -Path $WildcardFileSpec

foreach ($file in $files) {
    Write-Host "Processing file: $file"
    if ($Operation -eq "*") {
        Perform-Actions -File $file.FullName
    } else {
        Perform-Action -Operation $Operation -File $file.FullName
    }
}
