# SAGA Unified Startup Script for PowerShell
Write-Host "Starting SAGA Unified..." -ForegroundColor Green
Write-Host ""

# Set Python path to current directory
$env:PYTHONPATH = $PWD

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Install dependencies if needed
if (-not (Test-Path "installed.flag")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    New-Item -Path "installed.flag" -ItemType File | Out-Null
}

# Run the application
Write-Host "Launching SAGA Unified..." -ForegroundColor Green
python main.py

# Keep window open if there's an error
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error occurred. Press any key to exit..." -ForegroundColor Red
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}