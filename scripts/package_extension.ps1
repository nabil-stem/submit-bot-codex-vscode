param(
    [string]$OutZip = ".\\release\\out\\submit-autoclicker-extension-upload.zip"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $repoRoot

$outDir = Split-Path -Parent $OutZip
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

if (Test-Path $OutZip) {
    Remove-Item -Force $OutZip
}

# Zip contents of extension so manifest.json is at zip root.
Compress-Archive -Path .\extension\* -DestinationPath $OutZip
Write-Host "Created: $OutZip" -ForegroundColor Green

