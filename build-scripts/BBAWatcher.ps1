# BBA Watcher Service
# Watches P:\bba-queue for .request files and runs BBA.exe
#
# To run at startup, create a shortcut to this script in:
#   shell:startup
# Or run: powershell -WindowStyle Hidden -File P:\build-scripts\BBAWatcher.ps1
#
# Protocol:
#   Mac creates:  {scenario}.request  (contains BBA command line arguments)
#   Watcher creates: {scenario}.starting (signals watcher is running)
#   Watcher runs BBA.exe
#   Watcher creates: {scenario}.done (contains "OK" or error message)
#   Watcher deletes: {scenario}.request and {scenario}.starting

$queuePath = "P:\bba-queue"
$pollInterval = 1  # seconds

Write-Host "BBA Watcher started. Watching $queuePath for .request files..."
Write-Host "Press Ctrl+C to stop."

while ($true) {
    # Look for .request files
    $requestFiles = Get-ChildItem -Path $queuePath -Filter "*.request" -ErrorAction SilentlyContinue

    foreach ($requestFile in $requestFiles) {
        $scenario = $requestFile.BaseName
        $requestPath = $requestFile.FullName
        $startingPath = Join-Path $queuePath "$scenario.starting"
        $donePath = Join-Path $queuePath "$scenario.done"

        Write-Host "$(Get-Date -Format 'HH:mm:ss') Processing: $scenario"

        # Create .starting file to signal we're working on it
        "Processing" | Out-File -FilePath $startingPath -Encoding utf8

        try {
            # Read parameters from request file (format: scenario,cc1,cc2)
            $content = Get-Content -Path $requestPath -Raw
            $parts = $content.Trim().Split(',')

            if ($parts.Count -ne 3) {
                throw "Invalid request format - expected: scenario,cc1,cc2"
            }

            $scenarioName = $parts[0].Trim()
            $cc1 = $parts[1].Trim()
            $cc2 = $parts[2].Trim()

            # Validate scenario name (alphanumeric, underscores, hyphens, spaces only)
            if ($scenarioName -notmatch '^[\w\s\-]+$') {
                throw "Invalid scenario name"
            }
            # Validate convention card names
            if ($cc1 -notmatch '^[\w\-]+$' -or $cc2 -notmatch '^[\w\-]+$') {
                throw "Invalid convention card name"
            }

            # Build the BBA command with fixed structure
            $inputFile = "P:\pbn\$scenarioName.pbn"
            $outputFile = "P:\bba\$scenarioName"
            $cc1File = "P:\bbsa\$cc1.bbsa"
            $cc2File = "P:\bbsa\$cc2.bbsa"

            $args = "--HAND `"$inputFile`" --ARCHIVE_FILE `"$outputFile`" --CC1 `"$cc1File`" --CC2 `"$cc2File`" --ARCHIVE_TYPE 4 --DD 0 --SD 1 --AUTOBID --AUTOCLOSE"

            Write-Host "  Running: BBA.exe $args"

            # Run BBA.exe and wait for completion, measuring elapsed time
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $process = Start-Process -FilePath "BBA.exe" -ArgumentList $args -Wait -PassThru
            $stopwatch.Stop()
            $elapsed = $stopwatch.Elapsed.ToString("mm\:ss")

            if ($process.ExitCode -eq 0) {
                [System.IO.File]::WriteAllText($donePath, "OK")
                Write-Host "  Completed successfully in $elapsed"
            } else {
                [System.IO.File]::WriteAllText($donePath, "ERROR: BBA.exe exited with code $($process.ExitCode)")
                Write-Host "  Failed with exit code $($process.ExitCode)"
            }
        }
        catch {
            $errorMsg = "ERROR: $($_.Exception.Message)"
            [System.IO.File]::WriteAllText($donePath, $errorMsg)
            Write-Host "  Exception: $($_.Exception.Message)"
        }
        finally {
            # Clean up request and starting files
            Remove-Item -Path $requestPath -ErrorAction SilentlyContinue
            Remove-Item -Path $startingPath -ErrorAction SilentlyContinue
        }
    }

    Start-Sleep -Seconds $pollInterval
}
