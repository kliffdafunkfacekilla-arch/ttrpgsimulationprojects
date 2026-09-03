@echo off
echo Starting S.A.G.A. Engine Boot Sequence...
echo =========================================
echo.

echo [1] Checking Ollama Service...
tasklist /fi "imagename eq ollama.exe" | find /i "ollama.exe" > nul
if %errorlevel% neq 0 (
    echo [!] Ollama is not running. Starting Ollama in the background...
    start /b ollama serve
    echo Waiting for Ollama to initialize...
    timeout /t 5 /nobreak > nul
) else (
    echo [OK] Ollama is already running.
)
echo.

echo [2] Launching S.A.G.A. B.R.U.T.A.L. Engine...
echo =========================================
python main_controller.py

if %errorlevel% neq 0 (
    echo.
    echo [CRITICAL ERROR] The Engine crashed. See output above.
    pause
)
