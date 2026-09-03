@echo off
TITLE SAGA World Architect
echo [LAUNCHER] Starting World Architect (Design Mode)...

if exist bin\TALEWEAVERS_Architect.exe (
    bin\TALEWEAVERS_Architect.exe
) else (
    echo [ERROR] Architect executable not found. Please run build.bat first.
)

pause
