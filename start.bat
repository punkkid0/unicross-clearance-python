@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\activate.bat" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
echo Starting UNICROSS clearance on http://localhost:5000
start "" "http://localhost:5000"
python run.py
