@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run setup.bat first.
  pause
  exit /b 1
)
echo Starting UNICROSS clearance on http://localhost:5000
start "" "http://localhost:5000"
".venv\Scripts\python.exe" run.py
