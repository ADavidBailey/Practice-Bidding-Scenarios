# A called ps1
$fileCount = 1

$nFiles = $global:nTestFiles
if ($fileCount -eq $nFiles) { break }

# The number of files for PowerScript programs
Write-Host "This is aCalled ps1 program speaking. nFiles =" $nFiles
