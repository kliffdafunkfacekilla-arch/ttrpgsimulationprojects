@echo off
echo ========================================================
echo          STARTING OMNIS AZGAAR NATIVE ENGINE
echo ========================================================

echo [1/2] Starting Python Omnis Backend (Port 8000)...
start "Omnis Backend" cmd /k "python server.py"

echo [2/2] Starting Azgaar's Fantasy Map Generator (Port 5173)...
start "Azgaar Core" cmd /k "npm run dev -- --port 5173"

echo ========================================================
echo Native Bridge Active! Open your browser to:
echo http://localhost:5173
echo ========================================================
pause
