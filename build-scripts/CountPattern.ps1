param (
    [string]$FileSpec,
    [string]$Pattern,
	[string]$Prefix
)

# Get all files matching the specified wildcard pattern, sorted alphabetically by name
$files = Get-ChildItem -Path $FileSpec -File | Sort-Object Name

# Loop through each file and count lines that match the pattern
foreach ($file in $files) {
    # Get the content of the file and count lines that match the pattern
    $count = (Get-Content -Path $file.FullName | Select-String -Pattern $Pattern).Count
    
    # Output the filename and count
    if (($Prefix -eq $null) -or ($Prefix -eq "")) {
		Write-Output "$count,$($file.Name)"
	}
	else {
		Write-Output "$Prefix,$($file.Name),$count"
	}
}
