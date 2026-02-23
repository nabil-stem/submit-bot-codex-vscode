param(
    [string]$PythonCmd = "python",
    [string]$ConfigPath = ".\\marketing\\launch_config.json",
    [switch]$SkipReleaseBuild
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "[growth] $Message" -ForegroundColor Cyan
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $repoRoot

Require-Command $PythonCmd

if (-not $SkipReleaseBuild) {
    Write-Step "Building release artifacts..."
    .\scripts\build_release.ps1
}

Write-Step "Generating launch/SEO copy kit..."
& $PythonCmd .\scripts\generate_launch_kit.py --config $ConfigPath --output .\marketing\out

Write-Step "Done."
Write-Host "Next actions:" -ForegroundColor Green
Write-Host "  1) Review marketing\\out\\launch_checklist.md"
Write-Host "  2) Optionally run .\\scripts\\apply_github_metadata.ps1 -DryRun"
Write-Host "  3) Use docs\\seo and docs\\store files to update GitHub + extension listing"
Write-Host "  4) Publish manually per platform rules (avoid bulk spam)"
