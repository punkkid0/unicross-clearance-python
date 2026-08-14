import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "unicross_clearance")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")

UPLOAD_DIR = ROOT / "uploads"
RECEIPT_DIR = UPLOAD_DIR / "receipts"
CERT_DIR = UPLOAD_DIR / "certificates"
PROFILE_DIR = UPLOAD_DIR / "profiles"
CREDENTIALS_DIR = UPLOAD_DIR / "credentials"

# Base fees for the specific units
FEES_INDIGENE = {
    "bursary": 75600,
    "library": 2000,
    "faculty": 5000,
    "department": 3000,
    "hostel": 15000,
    "student_affairs": 1500,
}

FEES_NON_INDIGENE = {
    "bursary": 81500,
    "library": 2000,
    "faculty": 5000,
    "department": 3000,
    "hostel": 15000,
    "student_affairs": 1500,
}

CLEARANCE_UNITS = [
    ("bursary", "Bursary"),
    ("library", "Library"),
    ("faculty", "Faculty"),
    ("department", "Department"),
    ("hostel", "Hostel"),
    ("student_affairs", "Student Affairs"),
]

ADMIN_ROLES = ["super_admin"] + [f"admin_{unit[0]}" for unit in CLEARANCE_UNITS]

def expected_fee(is_indigene: bool, unit_code: str = "bursary") -> int:
    fees = FEES_INDIGENE if is_indigene else FEES_NON_INDIGENE
    return fees.get(unit_code, 0)

