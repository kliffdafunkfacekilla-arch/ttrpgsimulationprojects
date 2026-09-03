@echo off
rem Change to the directory of this script
cd /d "%~dp0"

rem Activate the Python virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Ensure you have run the setup steps.
)

rem Run the main application
python main.py

pause
