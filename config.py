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

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "").strip()
PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY", "").strip()
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")

UPLOAD_DIR = ROOT / "uploads"
RECEIPT_DIR = UPLOAD_DIR / "receipts"
CERT_DIR = UPLOAD_DIR / "certificates"

FEE_INDIGENE = 75600
FEE_NON_INDIGENE = 81500

CLEARANCE_UNITS = [
    ("bursary", "Bursary"),
    ("library", "Library"),
    ("faculty", "Faculty"),
    ("department", "Department"),
    ("hostel", "Hostel"),
    ("student_affairs", "Student Affairs"),
]


def expected_fee(is_indigene: bool) -> int:
    return FEE_INDIGENE if is_indigene else FEE_NON_INDIGENE
