@echo off
echo ========================================================
echo         Launching Newyrr Automated Media Studio
echo ========================================================
echo.
cd /d "%~dp0"
start http://127.0.0.1:8080
python -m uvicorn app:app --host 127.0.0.1 --port 8080 --reload
pause
