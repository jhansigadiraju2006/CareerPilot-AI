@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo        CareerPilot AI - Setup and Run
echo ==========================================
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto error
)
echo Installing or checking Python dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo Starting CareerPilot AI at http://127.0.0.1:5000
".venv\Scripts\python.exe" app.py
goto end
:error
echo.
echo Setup failed. Confirm Python is installed and internet is available for dependency installation.
:end
pause
