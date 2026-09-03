# PowerShell wrapper for Fantasy Map Generator
# This script checks that required runtimes and dependencies are present,
# installs them if necessary, and then launches the original startup.bat.

function Write-Info($msg) {
    Write-Host $msg -ForegroundColor Cyan
}
function Write-ErrorAndExit($msg) {
    Write-Host $msg -ForegroundColor Red
    exit 1
}

Write-Info "=== Checking Python installation ==="
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-ErrorAndExit "Python is not installed or not on PATH. Please install Python 3.x from https://python.org and restart this script."
}
Write-Info "Python found: $($pythonCmd.Path)"

Write-Info "=== Checking Node.js installation ==="
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $nodeCmd -or -not $npmCmd) {
    Write-ErrorAndExit "Node.js and/or npm are missing. Install them from https://nodejs.org and ensure they are on PATH."
}
Write-Info "Node.js found: $($nodeCmd.Path)"
Write-Info "npm found: $($npmCmd.Path)"

# Ensure Python dependencies are installed
Write-Info "=== Installing Python requirements ==="
$reqFile = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $reqFile) {
    python -m pip install -r $reqFile
    if ($LASTEXITCODE -ne 0) { Write-ErrorAndExit "Failed to install Python requirements." }
} else {
    Write-Info "No requirements.txt found, skipping Python package install."
}

# Ensure npm dependencies are installed
Write-Info "=== Installing npm dependencies ==="
$packageJson = Join-Path $PSScriptRoot "package.json"
if (Test-Path $packageJson) {
    if (-not (Test-Path (Join-Path $PSScriptRoot "node_modules"))) {
        npm install
        if ($LASTEXITCODE -ne 0) { Write-ErrorAndExit "npm install failed." }
    } else {
        Write-Info "node_modules folder already exists, skipping npm install."
    }
} else {
    Write-Info "package.json not found, skipping npm install."
}

# Launch the original batch file
Write-Info "=== Launching startup.bat ==="
$batPath = Join-Path $PSScriptRoot "startup.bat"
if (Test-Path $batPath) {
    # Use cmd.exe to run the batch file so its internal commands work as expected
    cmd /c ""$batPath""
} else {
    Write-ErrorAndExit "startup.bat not found in the project root."
}
