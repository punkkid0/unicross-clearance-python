# Install (Python version)

You need a Windows PC, internet, **Python 3.11+**, and **PostgreSQL**.

You do **not** need Node.js for this project.

## 1. Download this folder

On GitHub: **Code → Download ZIP**, unzip it.  
Or: `git clone` this repository.

## 2. Install Python

https://www.python.org/downloads/  
During setup, tick **Add python.exe to PATH**.

## 3. Install PostgreSQL

https://www.postgresql.org/download/windows/  
Write down the **postgres** user password.

## 4. Put the folder in a simple path, then double-click `setup.bat`

Do **not** run it from a copied “backup files” folder if a `.venv` from another location is still inside.

Best location example:

`C:\Users\user\Desktop\unicross-clearance-python`

If setup failed once, delete the `.venv` folder, then double-click `setup.bat` again.

If the window shows **Successfully installed** and then still says it failed, that was an old script bug. Use the latest `setup.bat` from GitHub. It continues when the packages actually installed.

## 5. Double-click `setup.bat`

It will:

- create a Python virtual environment (`.venv`)
- `pip install` everything in `requirements.txt`
- create `.env`
- ask for the PostgreSQL password
- create database `unicross_clearance`
- add demo admin and student

## 6. Double-click `start.bat`

Browser: **http://localhost:5000**

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Student | `student1` | `student123` |

## Manual commands (if you do not want the .bat)

```powershell
cd C:\Users\HP\Desktop\unicross-clearance-python
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
notepad .env
python setup_db.py
python run.py
```

## If it fails

| Problem | Fix |
|---|---|
| `python` not found | Reinstall Python with PATH ticked, open a new window |
| Database password error | Same password as PostgreSQL installer, saved in `.env` |
| `ECONNREFUSED` | Start the PostgreSQL Windows service |
