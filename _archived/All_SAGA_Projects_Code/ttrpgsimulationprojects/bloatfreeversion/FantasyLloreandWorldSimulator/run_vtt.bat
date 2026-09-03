@echo off
TITLE SAGA Tactical VTT Launcher
echo [LAUNCHER] Starting S.A.G.A. Engine (Arcade VTT)...

:: Launch as a module to handle relative imports
python -m saga_engine.main

pause
