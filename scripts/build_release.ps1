param(
    [string]$OutputDir = ".\\release\\out",
    [switch]$NoZip
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "[release] $Message" -ForegroundColor Cyan
}

function Ensure-Directory([string]$Path) {
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Copy-ProjectTree([string]$SourceRoot, [string]$DestinationRoot) {
    $excludedDirNames = @("__pycache__", ".pytest_cache", ".venv", ".mypy_cache", ".ruff_cache", ".git")
    $excludedFilePatterns = @("*.pyc", "*.pyo")

    Ensure-Directory $DestinationRoot

    $resolvedSourceRoot = (Resolve-Path -Path $SourceRoot).Path

    $sourceUri = New-Object System.Uri(($resolvedSourceRoot.TrimEnd("\") + "\"))

    $files = Get-ChildItem -Path $resolvedSourceRoot -Recurse -File | Where-Object {
        $path = $_.FullName
        foreach ($name in $excludedDirNames) {
            if ($path -match "\\$([regex]::Escape($name))(\\|$)") {
                return $false
            }
        }
        foreach ($pattern in $excludedFilePatterns) {
            if ($_.Name -like $pattern) {
                return $false
            }
        }
        return $true
    }

    foreach ($file in $files) {
        $fileUri = New-Object System.Uri($file.FullName)
        $relative = [System.Uri]::UnescapeDataString($sourceUri.MakeRelativeUri($fileUri).ToString()).Replace("/", "\")
        $destination = Join-Path $DestinationRoot $relative
        $parent = Split-Path -Parent $destination
        Ensure-Directory $parent
        Copy-Item -Path $file.FullName -Destination $destination -Force
    }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$outputRoot = Resolve-Path -Path (Join-Path $repoRoot $OutputDir) -ErrorAction SilentlyContinue
if (-not $outputRoot) {
    Ensure-Directory (Join-Path $repoRoot $OutputDir)
    $outputRoot = Resolve-Path -Path (Join-Path $repoRoot $OutputDir)
}
$outputRoot = $outputRoot.Path

$stagingDir = Join-Path $outputRoot "staging"
$desktopStage = Join-Path $stagingDir "submit-autoclicker-desktop"
$extensionStage = Join-Path $stagingDir "submit-autoclicker-extension"

Write-Step "Cleaning staging directory..."
if (Test-Path $stagingDir) {
    Remove-Item -Recurse -Force $stagingDir
}
Ensure-Directory $desktopStage
Ensure-Directory $extensionStage

Write-Step "Copying desktop project..."
Copy-ProjectTree -SourceRoot (Join-Path $repoRoot "desktop") -DestinationRoot $desktopStage

Write-Step "Copying extension project..."
Copy-ProjectTree -SourceRoot (Join-Path $repoRoot "extension") -DestinationRoot $extensionStage

Write-Step "Copying root docs..."
Copy-Item -Path (Join-Path $repoRoot "README.md") -Destination (Join-Path $stagingDir "README.md") -Force

if (-not $NoZip) {
    $desktopZip = Join-Path $outputRoot "submit-autoclicker-desktop.zip"
    $extensionZip = Join-Path $outputRoot "submit-autoclicker-extension.zip"
    $bundleZip = Join-Path $outputRoot "submit-autoclicker-bundle.zip"

    Write-Step "Creating desktop ZIP..."
    if (Test-Path $desktopZip) { Remove-Item -Force $desktopZip }
    Compress-Archive -Path (Join-Path $desktopStage "*") -DestinationPath $desktopZip

    Write-Step "Creating extension ZIP..."
    if (Test-Path $extensionZip) { Remove-Item -Force $extensionZip }
    Compress-Archive -Path (Join-Path $extensionStage "*") -DestinationPath $extensionZip

    Write-Step "Creating combined bundle ZIP..."
    if (Test-Path $bundleZip) { Remove-Item -Force $bundleZip }
    Compress-Archive -Path (Join-Path $stagingDir "*") -DestinationPath $bundleZip
}

Write-Step "Release packaging complete."
Write-Host "Output directory: $outputRoot" -ForegroundColor Green
