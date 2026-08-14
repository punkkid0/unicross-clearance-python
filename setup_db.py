"""Create the database, apply schema, and seed demo users."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import bcrypt
import pg8000.dbapi

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "unicross_clearance")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

if not DB_PASSWORD or "your_password" in DB_PASSWORD:
    print("Set DB_PASSWORD in .env first.")
    sys.exit(1)


def hash_pw(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def connect(dbname):
    return pg8000.dbapi.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=dbname,
    )


def main():
    admin = connect("postgres")
    admin.autocommit = True
    cur = admin.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone() is None:
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"Created database {DB_NAME}")
    else:
        print(f"Database {DB_NAME} already exists")
    cur.close()
    admin.close()

    conn = connect(DB_NAME)
    conn.autocommit = True
    cur = conn.cursor()
    schema = (ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    
    # Drop existing tables to apply the new schema cleanly
    cur.execute("""
        DROP TABLE IF EXISTS audit_log CASCADE;
        DROP TABLE IF EXISTS clearance_units CASCADE;
        DROP TABLE IF EXISTS clearance_requests CASCADE;
        DROP TABLE IF EXISTS transactions CASCADE;
        DROP TABLE IF EXISTS payments CASCADE;
        DROP TABLE IF EXISTS school_fee_payments CASCADE;
        DROP TABLE IF EXISTS departments CASCADE;
        DROP TABLE IF EXISTS students CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
    """)

    # pg8000 executes one statement; split on semicolons carefully
    for stmt in split_sql(schema):
        cur.execute(stmt)
    print("Schema applied")

    cur.execute(
        """INSERT INTO users (username, email, password_hash, full_name, role)
           VALUES (%s, %s, %s, %s, 'super_admin')
           ON CONFLICT (username) DO UPDATE SET role = 'super_admin'""",
        ("admin", "admin@school.edu", hash_pw("admin123"), "Super Admin"),
    )
    # Seed department admins
    from config import CLEARANCE_UNITS
    for code, name in CLEARANCE_UNITS:
        cur.execute(
            """INSERT INTO users (username, email, password_hash, full_name, role)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (username) DO UPDATE SET role = %s""",
            (f"admin_{code}", f"{code}@school.edu", hash_pw("admin123"), f"{name} Admin", f"admin_{code}", f"admin_{code}"),
        )
    print("Seeded super_admin and department admins (password: admin123)")

    cur.execute("SELECT id FROM users WHERE username = %s", ("student1",))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            """INSERT INTO users (username, email, password_hash, full_name, role)
               VALUES (%s, %s, %s, %s, 'student') RETURNING id""",
            ("student1", "student1@school.edu", hash_pw("student123"), "Test Student"),
        )
        uid = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO students (user_id, matric_no, is_indigene)
               VALUES (%s, %s, TRUE) RETURNING id""",
            (uid, "22/CSC/124"),
        )
        sid = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO payments (rrr, student_id, amount, payment_type, payment_method, notes)
               VALUES (%s, %s, %s, 'bursary', 'remita', 'Demo official payment for student1')
               ON CONFLICT (rrr) DO NOTHING""",
            ("RRR-STUDENT1-001234567890", sid, 75600),
        )
        print("Seeded student1 / student123 + demo RRR")
    else:
        print("student1 already exists")

    cur.close()
    conn.close()
    print("Done.")


def split_sql(text: str):
    parts = []
    buf = []
    for line in text.splitlines():
        if line.strip().startswith("--"):
            continue
        buf.append(line)
        if line.strip().endswith(";"):
            stmt = "\n".join(buf).strip().rstrip(";")
            if stmt:
                parts.append(stmt)
            buf = []
    tail = "\n".join(buf).strip().rstrip(";")
    if tail:
        parts.append(tail)
    return parts


if __name__ == "__main__":
    main()
