param(
    [string]$PythonCmd = "python",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Message) {
    Write-Host "[setup] $Message" -ForegroundColor Cyan
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

Write-Step "Validating prerequisites..."
Require-Command $PythonCmd

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktopDir = Join-Path $repoRoot "desktop"
$venvDir = Join-Path $desktopDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\\python.exe"

Write-Step "Preparing virtual environment..."
if (-not (Test-Path $venvPython)) {
    & $PythonCmd -m venv $venvDir
}

Write-Step "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

Write-Step "Installing desktop dependencies..."
& $venvPython -m pip install -r (Join-Path $desktopDir "requirements.txt")

if (-not $SkipTests) {
    Write-Step "Running desktop tests..."
    Push-Location $desktopDir
    try {
        & $venvPython -m pytest -q
    }
    finally {
        Pop-Location
    }
}

Write-Step "Setup completed."
Write-Host ""
Write-Host "Run desktop mode:" -ForegroundColor Green
Write-Host "  cd desktop"
Write-Host "  .venv\\Scripts\\Activate.ps1"
Write-Host "  python main.py"
Write-Host ""
Write-Host "Load extension mode from folder: extension\\" -ForegroundColor Green

