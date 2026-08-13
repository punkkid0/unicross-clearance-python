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

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed.
  echo Download Python 3.11+ from https://www.python.org/downloads/
  echo Tick "Add python.exe to PATH" during install, then run this file again.
  start "" "https://www.python.org/downloads/"
  pause
  exit /b 1
)

python -m venv .venv
if errorlevel 1 (
  echo Could not create a virtual environment.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo pip install failed. Check your internet connection.
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
if defined DBPASS if not "!DBPASS!"=="your_password" (
  echo .env already has a password.
  set /p KEEP="Keep it? (Y/n): "
  if /I not "!KEEP!"=="n" goto :rundb
)
set /p DBPASS="PostgreSQL password: "

set "SECRET="
for /f "usebackq delims=" %%H in (`python -c "import secrets; print(secrets.token_hex(32))"`) do set "SECRET=%%H"

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
  echo PAYSTACK_SECRET_KEY=
  echo PAYSTACK_PUBLIC_KEY=
  echo BASE_URL=http://localhost:5000
)

:rundb
echo.
echo Creating database and demo users...
python setup_db.py
if errorlevel 1 (
  echo Database setup failed. Is PostgreSQL running? Is the password correct?
  pause
  exit /b 1
)

echo.
echo Setup finished.
echo Next: double-click start.bat
echo Then open http://localhost:5000
echo   Admin    admin / admin123
echo   Student  student1 / student123
echo.
pause
