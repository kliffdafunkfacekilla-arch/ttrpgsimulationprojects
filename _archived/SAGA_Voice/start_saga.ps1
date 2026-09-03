Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "      PROJECT S.A.G.A. - LAUNCHER         " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -Path $scriptPath

Write-Host "`n[1/3] Starting Configuration Launcher..." -ForegroundColor Yellow
$process = Start-Process -NoNewWindow -PassThru -Wait -FilePath "python" -ArgumentList "-m", "frontend.main_menu"

Write-Host "`n[2/3] Starting Tag-Driven UI Renderer (Background)..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "frontend.app"

Write-Host "[3/3] Starting AI Voice Engine..." -ForegroundColor Yellow
python voice_engine.py

Write-Host "`nSAGA Voice Engine has terminated." -ForegroundColor Red
Read-Host -Prompt "Press Enter to exit"
