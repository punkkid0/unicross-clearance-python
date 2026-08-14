from functools import wraps
from flask import g, redirect, url_for, flash
from app.db import query
import bcrypt
import config


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def valid_password(pw: str) -> str | None:
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    if not any(c.isalpha() for c in pw) or not any(c.isdigit() for c in pw):
        return "Password must contain at least one letter and one number."
    return None


def login_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not g.user:
                flash("Please log in first.", "error")
                return redirect(url_for("auth.login"))
            if roles and g.user["role"] not in roles:
                # If they are super_admin, let them access any admin route. But not student routes.
                if g.user["role"] == "super_admin" and any(r.startswith("admin") for r in roles):
                    pass # super admin gets access
                else:
                    flash("You do not have access to that page.", "error")
                    return redirect(url_for("auth.home"))
            return fn(*args, **kwargs)
        return wrapper
    return deco


def student_record(user_id=None):
    uid = user_id or g.user["id"]
    return query(
        """SELECT s.*, u.username, u.email, u.full_name, u.role
           FROM students s JOIN users u ON u.id = s.user_id
           WHERE s.user_id = %s""",
        (uid,),
        fetch="one",
    )


def log_action(action, details=""):
    if g.get("user"):
        query(
            "INSERT INTO audit_log (action, user_id, details) VALUES (%s, %s, %s)",
            (action, g.user["id"], details),
            fetch="none",
        )


def unit_label(code):
    return dict(config.CLEARANCE_UNITS).get(code, code)
