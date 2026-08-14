# Setup & Installation Guide

Follow these instructions strictly to get the UNICROSS Clearance system running on your laptop.

---

## 1. Prerequisites (What to Install)

Before running the code, you **must** install the following software on your Windows machine:

1. **Python (Version 3.10 or higher)**
   - Download the official installer from python.org.
   - **CRITICAL STEP:** During installation, you MUST check the box that says **"Add Python to PATH"** at the bottom of the installation window before clicking "Install Now".

2. **PostgreSQL (Version 15 or 16)**
   - Download the Windows installer from the official PostgreSQL website.
   - **CRITICAL STEP:** During the installation, it will ask you to create a master password for the default `postgres` user. You must set this password exactly to **`postgres`** (all lowercase). If you set it to anything else, the Python code will crash because it won't be able to log in!

3. **VS Code (Optional but Recommended)**
   - Download Visual Studio Code to easily open the project folder and use the built-in terminal.

---

## 2. Database Setup

Once PostgreSQL is installed, you need to create the specific database for this project:

1. Open **pgAdmin 4** (this installed automatically when you installed PostgreSQL).
2. It will ask for your master password. Type in `postgres`.
3. On the left sidebar, click the dropdown arrow next to **Servers** -> **PostgreSQL**.
4. Right-click on **Databases**, select **Create** -> **Database...**
5. In the "Database" name field, type exactly: **`unicross_db`**
6. Click **Save**.

You now have a blank database waiting for the code!

---

## 3. How to Run the Code

Now that your database is ready, you need to start the application:

1. Open the `unicross-clearance-python` folder in **VS Code**.
2. Go to the top menu, click **Terminal** -> **New Terminal**.
3. Run the following commands one by one in the terminal:

**Step 3a: Create a virtual environment**
```bash
python -m venv .venv
```

**Step 3b: Activate the virtual environment**
```bash
.\.venv\Scripts\activate
```
*(You will know this worked if you see `(.venv)` appear on the left side of your terminal line).*

**Step 3c: Install all required Python packages**
```bash
pip install -r requirements.txt
```

**Step 3d: Initialize the database tables**
```bash
python setup_db.py
```
*(This command will connect to PostgreSQL, create all the required tables in `unicross_db`, and automatically create the default Admin and Student accounts for you).*

**Step 3e: Start the Server**
```bash
python run.py
```

---

## 4. Accessing the Site

Once the terminal says `Running on http://127.0.0.1:5000`, open your web browser (Chrome, Edge, etc.) and go to:
**`http://localhost:5000`**

**Default Accounts you can use:**
- **Super Admin:** Username: `admin` | Password: `admin123`
- **Library Admin:** Username: `admin_library` | Password: `admin123`
- **Student 1:** Username: `student1` | Password: `password123`
