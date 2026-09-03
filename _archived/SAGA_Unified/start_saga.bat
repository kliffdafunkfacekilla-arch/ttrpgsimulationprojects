@echo off
REM SAGA Unified Startup Script for Windows
echo Starting SAGA Unified...
echo.

REM Set Python path to current directory
set PYTHONPATH=%CD%

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install dependencies if needed
if not exist "installed.flag" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo. > installed.flag
)

REM Run the application
echo Launching SAGA Unified...
python main.py

pause