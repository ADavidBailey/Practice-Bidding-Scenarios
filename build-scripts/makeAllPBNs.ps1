# Define the path to the root directory containing the nested folders and files
$rootPath = "P:\dlr\"

# Define the path to the script you want to call for each file
$scriptPath = "P:\build-scripts\makeOnePBN.cmd"

# Define the file extension/type you want to filter by (e.g., ".txt", ".csv", ".log")
$fileType = ".dlr"  # Change this to the desired file extension

# Get all files in the root directory and its subdirectories that match the specified file type
$files = Get-ChildItem -Path $rootPath -Recurse -File | Where-Object { $_.Extension -eq $fileType }
# Initialize a counter for processed files

$startLocation = Get-Location

Set-Location -Path $rootPath

$fileCount = 0

# Iterate through each filtered file and call the script
foreach ($file in $files) {
    # Output the current file being processed
    Write-Host "Processing file: $($file.FullName)"

    # Call the external script, passing the file path as an argument
    & $scriptPath $file.FullName

    # Increment the counter
    $fileCount++
    if ($fileCount -eq 3) { break }
}

# Display the number of files processed
Write-Host "Total number of files processed: $fileCount"

Set-Location -Path $startLocation
