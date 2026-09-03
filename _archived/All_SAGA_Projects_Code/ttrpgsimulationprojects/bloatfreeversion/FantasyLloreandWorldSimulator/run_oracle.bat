@echo off
TITLE SAGA Oracle Launcher
echo [LAUNCHER] Starting SAGA Brain (The Oracle)...

:: 1. Clear Port 8000 (SAGA Brain)
echo [LAUNCHER] Cleaning up any stale server processes on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: 2. Start Python Server
echo [LAUNCHER] Starting scripts/server.py...
python scripts/server.py

pause
