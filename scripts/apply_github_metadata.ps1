param(
    [string]$Repo = "nabilessaadiii-ship-it/submit-bot-codex-vscode",
    [string]$Website = "https://github.com/nabilessaadiii-ship-it/submit-bot-codex-vscode",
    [string]$Description = "",
    [string]$TopicsFile = ".\\marketing\\out\\github_topics.txt",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "[github-meta] $Message" -ForegroundColor Cyan
}

$hasGh = [bool](Get-Command gh -ErrorAction SilentlyContinue)
if ((-not $hasGh) -and (-not $DryRun)) {
    throw "GitHub CLI (gh) is required for non-dry runs."
}

if ([string]::IsNullOrWhiteSpace($Description)) {
    $descPath = ".\\marketing\\out\\github_description.txt"
    if (Test-Path $descPath) {
        $Description = (Get-Content $descPath -Raw).Trim()
    } else {
        $Description = "Safe VS Code Codex + Chrome/Edge submit auto-clicker with allowlists, dry-run mode, and visible automation status."
    }
}

$topics = @()
if (Test-Path $TopicsFile) {
    $topics = Get-Content $TopicsFile | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

Write-Step "Repo: $Repo"
Write-Step "Description: $Description"
Write-Step "Website: $Website"
Write-Step "Topics: $($topics -join ', ')"

if ($DryRun) {
    Write-Step "DryRun enabled. No API calls executed."
    return
}

Write-Step "Updating description/homepage..."
gh repo edit $Repo --description $Description --homepage $Website

if ($topics.Count -gt 0) {
    Write-Step "Applying topics..."
    foreach ($topic in $topics) {
        gh repo edit $Repo --add-topic $topic
    }
}

Write-Step "GitHub metadata update complete."
