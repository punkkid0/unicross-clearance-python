import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from app.db import query
from app.helpers import login_required, student_record, log_action
from app.verifier import analyze_receipt
from app.certificate import generate_certificate
import config

bp = Blueprint("student", __name__, url_prefix="/student")

ALLOWED = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@bp.route("/dashboard")
@login_required("student")
def dashboard():
    st = student_record()
    fee = config.expected_fee(bool(st["is_indigene"]))
    paid = query(
        """SELECT COALESCE(SUM(amount),0) AS total FROM school_fee_payments
           WHERE student_id = %s AND status = 'successful'""",
        (st["id"],),
        fetch="one",
    )
    requests = query(
        """SELECT * FROM clearance_requests WHERE student_id = %s
           ORDER BY created_at DESC""",
        (st["id"],),
    )
    latest = requests[0] if requests else None
    units = []
    if latest:
        units = query(
            "SELECT * FROM clearance_units WHERE request_id = %s ORDER BY id",
            (latest["id"],),
        )
    return render_template(
        "student/dashboard.html",
        student=st,
        fee=fee,
        paid=float(paid["total"]),
        requests=requests,
        latest=latest,
        unit_rows=units,
    )


@bp.route("/profile", methods=["GET", "POST"])
@login_required("student")
def profile():
    st = student_record()
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        matric = (request.form.get("matric_no") or "").strip() or None
        if not full_name or not email:
            flash("Name and email are required.", "error")
        else:
            taken = query(
                "SELECT id FROM users WHERE email = %s AND id <> %s",
                (email, g.user["id"]),
                fetch="one",
            )
            if taken:
                flash("That email is already in use.", "error")
            else:
                query(
                    "UPDATE users SET full_name = %s, email = %s WHERE id = %s",
                    (full_name, email, g.user["id"]),
                    fetch="none",
                )
                query(
                    "UPDATE students SET matric_no = %s WHERE id = %s",
                    (matric, st["id"]),
                    fetch="none",
                )
                flash("Profile updated.", "success")
                return redirect(url_for("student.profile"))
        st = student_record()
    return render_template(
        "student/profile.html",
        student=st,
        fee=config.expected_fee(bool(st["is_indigene"])),
    )


@bp.route("/clearance", methods=["GET", "POST"])
@login_required("student")
def clearance():
    st = student_record()
    fee = config.expected_fee(bool(st["is_indigene"]))
    pending = query(
        "SELECT id FROM clearance_requests WHERE student_id = %s AND status = 'pending'",
        (st["id"],),
        fetch="one",
    )
    if request.method == "POST":
        if pending:
            flash("You already have a pending clearance request.", "error")
            return redirect(url_for("student.clearance"))
        rrr = (request.form.get("payment_reference") or "").strip()
        amount = request.form.get("declared_amount") or ""
        file = request.files.get("receipt")
        if not rrr or len(rrr) < 5:
            flash("Official payment reference (RRR) is required.", "error")
            return render_template("student/clearance.html", student=st, fee=fee, pending=pending)
        try:
            declared = float(amount)
        except ValueError:
            flash("Enter a valid amount.", "error")
            return render_template("student/clearance.html", student=st, fee=fee, pending=pending)
        if abs(declared - fee) >= 1:
            flash(f"Amount must be exactly N{fee:,.0f} for your indigene status.", "error")
            return render_template("student/clearance.html", student=st, fee=fee, pending=pending)
        if not file or not file.filename:
            flash("Receipt image is required.", "error")
            return render_template("student/clearance.html", student=st, fee=fee, pending=pending)
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED:
            flash("Receipt must be an image (JPG, PNG, GIF, WebP).", "error")
            return render_template("student/clearance.html", student=st, fee=fee, pending=pending)

        safe = secure_filename(file.filename)
        stored = f"receipt-{st['id']}-{safe}"
        dest = config.RECEIPT_DIR / stored
        file.save(dest)

        result = analyze_receipt(st, declared, rrr, str(dest))
        req = query(
            """INSERT INTO clearance_requests
               (student_id, receipt_path, receipt_hash, declared_amount, payment_reference,
                status, auto_score, auto_decision, auto_reasons)
               VALUES (%s, %s, %s, %s, %s, 'pending', %s, %s, %s)
               RETURNING id""",
            (
                st["id"],
                f"/uploads/receipts/{stored}",
                result["file_hash"],
                declared,
                rrr,
                result["score"],
                result["decision"],
                json.dumps(result["reasons"]),
            ),
            fetch="one",
        )
        for code, _name in config.CLEARANCE_UNITS:
            query(
                """INSERT INTO clearance_units (request_id, unit_code, status)
                   VALUES (%s, %s, 'pending')""",
                (req["id"], code),
                fetch="none",
            )
        log_action("clearance_submitted", f"request {req['id']} score={result['score']}")
        flash(
            f"Request submitted. Automatic check: {result['decision']} ({result['score']}/100).",
            "success",
        )
        return redirect(url_for("student.dashboard"))

    history = query(
        """SELECT * FROM clearance_requests WHERE student_id = %s
           ORDER BY created_at DESC""",
        (st["id"],),
    )
    return render_template(
        "student/clearance.html",
        student=st,
        fee=fee,
        pending=pending,
        history=history,
    )


@bp.route("/request/<int:rid>")
@login_required("student")
def request_detail(rid):
    st = student_record()
    req = query(
        "SELECT * FROM clearance_requests WHERE id = %s AND student_id = %s",
        (rid, st["id"]),
        fetch="one",
    )
    if not req:
        flash("Request not found.", "error")
        return redirect(url_for("student.dashboard"))
    units = query(
        "SELECT * FROM clearance_units WHERE request_id = %s ORDER BY id",
        (rid,),
    )
    reasons = []
    if req["auto_reasons"]:
        try:
            reasons = json.loads(req["auto_reasons"])
        except json.JSONDecodeError:
            reasons = [req["auto_reasons"]]
    return render_template(
        "student/request.html",
        req=req,
        units=units,
        reasons=reasons,
        student=st,
    )
