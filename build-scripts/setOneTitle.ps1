param(
    [string]$ScenarioName
)

$filePath = "P:\dlr\" + $ScenarioName + ".dlr"

# Verify if file exists
if (-not (Test-Path -Path $filePath)) {
    Write-Host "File not found: $filePath"
    exit
}

# Read the file and search for the scenario-title line
$ScenarioTitle = Select-String -Path $filePath -Pattern "scenario-title:" -SimpleMatch |
    ForEach-Object {
        # Extract the title text after 'scenario-title:'
        $_.Line -replace "\# scenario-title:\s*", ""
    }

# Display the ScenarioTitle or notify if it wasn't found
if ($ScenarioTitle) {
#    Write-Host "Scenario Title: $ScenarioTitle"
	& "BridgeComposer.exe" P:\bba\$ScenarioName.pbn /event "$ScenarioTitle" /save P:\bba\$ScenarioName.pbn
	Wait-Process -Name "BridgeComposer"
} else {
    Write-Host "No scenario title found in the file."
}
