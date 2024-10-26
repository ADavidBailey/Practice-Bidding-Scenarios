# A called ps1
$fileCount = 1

$nFiles = $global:nTestFiles
if ($fileCount -eq $nFiles) { break }

# The number of files for PowerScript programs
Write-Host "Hello, World!  This is abbTest.ps1" $nFiles
