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

REM A copied/moved .venv keeps the OLD computer path inside pip.exe.
REM That looks like an internet error. Always rebuild the venv here.
if exist ".venv\" (
  echo Removing old virtual environment so it matches THIS folder...
  rmdir /s /q ".venv" 2>nul
)

echo Creating a new virtual environment...
python -m venv ".venv"
if errorlevel 1 (
  echo Could not create a virtual environment.
  echo If this folder was copied, make sure you can write files here.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment is missing python.exe. Setup cannot continue.
  pause
  exit /b 1
)

echo Installing packages with python -m pip (this needs internet)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo Could not upgrade pip.
  echo This can be a proxy, antivirus, or a blocked pypi.org — not always "no internet".
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m pip install -r "%CD%\requirements.txt"
if errorlevel 1 (
  echo.
  echo Package install failed.
  echo Real cause is printed ABOVE this line. It is usually:
  echo   - project folder was moved and an old .venv was reused  (fixed by this script)
  echo   - Python is too new / a package has no Windows wheel
  echo   - pip cannot reach https://pypi.org
  echo   - the folder path has unusual permissions
  echo.
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
  echo PAYSTACK_SECRET_KEY=
  echo PAYSTACK_PUBLIC_KEY=
  echo BASE_URL=http://localhost:5000
)

:rundb
echo.
echo Creating database and demo users...
".venv\Scripts\python.exe" "%CD%\setup_db.py"
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
