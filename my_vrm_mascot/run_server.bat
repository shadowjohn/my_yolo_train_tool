@echo off
setlocal
cd /d "%~dp0"

echo.
echo ==================================
echo   My VRM Mascot Local Server
echo ==================================
echo.
echo Portal: http://127.0.0.1:8765/portal.html
echo Main:   http://127.0.0.1:8765/
echo.

python server.py
pause
