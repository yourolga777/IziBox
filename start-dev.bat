@echo off
echo Starting BizInbox development servers...

:: Start backend in a new window
start "BizInbox Backend" cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --reload --port 7911"

:: Wait for backend to initialize
timeout /t 3 /nobreak >nul

:: Start frontend in a new window
start "BizInbox Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Backend: http://localhost:7911
echo Frontend: http://localhost:5173
echo.
echo Close the terminal windows to stop the servers.
pause
