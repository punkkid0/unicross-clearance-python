@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title UNICROSS Clearance (Python) — setup

echo.
echo ============================================================
echo   UNICROSS Payment Verification ^& Clearance
echo   Python + HTML/CSS/JS + PostgreSQL
echo ============================================================
echo.
echo Project folder:
echo   %CD%
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed.
  echo Download Python 3.11+ from https://www.python.org/downloads/
  echo Tick "Add python.exe to PATH" during install, then run this file again.
  start "" "https://www.python.org/downloads/"
  pause
  exit /b 1
)

echo Python found:
python -V
echo.

if exist ".venv\" (
  echo Removing old virtual environment so it matches THIS folder...
  rmdir /s /q ".venv" 2>nul
)

echo Creating a new virtual environment...
python -m venv ".venv"
if not exist ".venv\Scripts\python.exe" (
  echo Could not create a virtual environment.
  pause
  exit /b 1
)

echo Installing packages (this needs internet)...
".venv\Scripts\python.exe" -m pip install --upgrade pip --disable-pip-version-check
".venv\Scripts\python.exe" -m pip install -r "%CD%\requirements.txt" --disable-pip-version-check

echo.
echo Checking that the main packages imported...
".venv\Scripts\python.exe" -c "import flask, dotenv, pg8000, bcrypt, reportlab; print('Packages OK')"
if errorlevel 1 (
  echo.
  echo Packages did not import. Scroll up for the real pip error.
  pause
  exit /b 1
)

if not exist ".env" copy /Y ".env.example" ".env" >nul

set "DBPASS="
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="DB_PASSWORD" set "DBPASS=%%B"
)

echo.
echo Enter the PostgreSQL "postgres" user password.
echo (The password you typed when you installed PostgreSQL.)
if defined DBPASS if not "!DBPASS!"=="your_password" (
  echo .env already has a password.
  set /p KEEP="Keep it? (Y/n): "
  if /I not "!KEEP!"=="n" goto :rundb
)
set /p DBPASS="PostgreSQL password: "
if not defined DBPASS (
  echo No password entered.
  pause
  exit /b 1
)

set "SECRET="
for /f "usebackq delims=" %%H in (`".venv\Scripts\python.exe" -c "import secrets; print(secrets.token_hex(32))"`) do set "SECRET=%%H"

> ".env" (
  echo FLASK_SECRET_KEY=!SECRET!
  echo FLASK_DEBUG=1
  echo.
  echo DB_HOST=localhost
  echo DB_PORT=5432
  echo DB_NAME=unicross_clearance
  echo DB_USER=postgres
  echo DB_PASSWORD=!DBPASS!
  echo.
  echo BASE_URL=http://localhost:5000
)

:rundb
echo.
echo Creating database and demo users...
".venv\Scripts\python.exe" "%CD%\setup_db.py"
if errorlevel 1 (
  echo.
  echo Database setup failed.
  echo - Is PostgreSQL installed and running?
  echo - Did you type the same postgres password as during PostgreSQL install?
  pause
  exit /b 1
)

echo.
echo Setup finished.
echo Next: double-click start.bat
echo Then open http://localhost:5000
echo   Super admin  admin / admin123
echo   Student      student1 / student123
echo.
pause
