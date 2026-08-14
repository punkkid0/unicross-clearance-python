from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from app.db import query
from app.helpers import hash_password, check_password, valid_password, login_required

bp = Blueprint("auth", __name__)


@bp.route("/")
def home():
    if not g.user:
        return redirect(url_for("auth.login"))
    if g.user["role"] != "student":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("student.dashboard"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ident = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = query(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (ident, ident),
            fetch="one",
        )
        if not user or not check_password(password, user["password_hash"]):
            flash("Invalid username or password.", "error")
            return render_template("login.html")
        if not user["is_active"]:
            flash("This account is disabled.", "error")
            return render_template("login.html")
        session.clear()
        session["user_id"] = user["id"]
        flash(f"Welcome, {user['full_name']}.", "success")
        return redirect(url_for("auth.home"))
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        matric = (request.form.get("matric_no") or "").strip() or None

        if not full_name or not username or not email:
            flash("Name, username and email are required.", "error")
            return render_template("register.html")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        err = valid_password(password)
        if err:
            flash(err, "error")
            return render_template("register.html")
        if query("SELECT id FROM users WHERE email = %s", (email,), fetch="one"):
            flash("Email already registered.", "error")
            return render_template("register.html")
        if query("SELECT id FROM users WHERE username = %s", (username,), fetch="one"):
            flash("Username already taken.", "error")
            return render_template("register.html")

        hashed = hash_password(password)
        user = query(
            """INSERT INTO users (username, email, password_hash, full_name, role)
               VALUES (%s, %s, %s, %s, 'student')
               RETURNING id""",
            (username, email, hashed, full_name),
            fetch="one",
        )
        query(
            """INSERT INTO students (user_id, matric_no) VALUES (%s, %s)""",
            (user["id"], matric),
            fetch="none",
        )
        session.clear()
        session["user_id"] = user["id"]
        flash("Account created. You can now request clearance after payment.", "success")
        return redirect(url_for("student.dashboard"))
    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/password", methods=["GET", "POST"])
@login_required()
def change_password():
    if request.method == "POST":
        current = request.form.get("current_password") or ""
        new_pw = request.form.get("new_password") or ""
        confirm = request.form.get("confirm_password") or ""
        if not check_password(current, g.user["password_hash"]):
            flash("Current password is wrong.", "error")
            return render_template("password.html")
        if new_pw != confirm:
            flash("New passwords do not match.", "error")
            return render_template("password.html")
        err = valid_password(new_pw)
        if err:
            flash(err, "error")
            return render_template("password.html")
        query(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (hash_password(new_pw), g.user["id"]),
            fetch="none",
        )
        flash("Password changed.", "success")
        return redirect(url_for("auth.home"))
    return render_template("password.html")
