@echo off
echo ==============================================
echo 🌍 Starting Omnis World Engine
echo ==============================================

echo [1/2] Starting Python FastAPI Backend on port 8000...
start "Omnis Backend" cmd /c "python server.py"

echo [2/2] Starting Vite Frontend on port 5173...
start "Omnis Frontend" cmd /c "npm run dev"

echo.
echo ==============================================
echo ✅ All systems launching!
echo.
echo Please wait a few seconds for the servers to boot up.
echo - The backend will run at: http://localhost:8000
echo - The frontend will run at: http://localhost:5173
echo.
echo Once the Vite server is ready, it will usually open 
echo your browser automatically. If not, open localhost:5173 manually.
echo ==============================================
pause
