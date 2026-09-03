@echo off
echo ==========================================
echo       PROJECT S.A.G.A. - LAUNCHER
echo ==========================================

cd /d "%~dp0"

echo [1/3] Starting Configuration Launcher...
python -m frontend.main_menu

echo [2/3] Starting Tag-Driven UI Renderer...
start "SAGA Frontend" /B python -m frontend.app

echo [3/3] Starting AI Voice Engine...
python voice_engine.py

echo SAGA Voice Engine has terminated.
pause
