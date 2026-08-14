import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from app.db import query
from app.helpers import login_required, student_record, log_action
from app.verifier import analyze_receipt
import config

bp = Blueprint("student", __name__, url_prefix="/student")

ALLOWED = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

@bp.route("/dashboard")
@login_required("student")
def dashboard():
    st = student_record()
    # Calculate all expected fees
    expected_fees = {u[0]: config.expected_fee(bool(st["is_indigene"]), u[0]) for u in config.CLEARANCE_UNITS}
    total_expected = sum(expected_fees.values())

    paid = query(
        """SELECT COALESCE(SUM(amount),0) AS total FROM payments
           WHERE student_id = %s AND status = 'completed'""",
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
        total_expected=total_expected,
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
                profile_pic_path = g.user.get("profile_pic_path")
                
                pic_file = request.files.get("profile_pic")
                if pic_file and pic_file.filename:
                    ext = "." + pic_file.filename.rsplit(".", 1)[-1].lower() if "." in pic_file.filename else ""
                    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
                        safe = secure_filename(pic_file.filename)
                        stored = f"profile-{g.user['id']}-{safe}"
                        dest = config.PROFILE_DIR / stored
                        pic_file.save(dest)
                        profile_pic_path = f"/uploads/profiles/{stored}"
                    else:
                        flash("Profile picture must be an image.", "error")

                query(
                    "UPDATE users SET full_name = %s, email = %s, profile_pic_path = %s WHERE id = %s",
                    (full_name, email, profile_pic_path, g.user["id"]),
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
    return render_template("student/profile.html", student=st)

@bp.route("/clearance", methods=["GET", "POST"])
@login_required("student")
def clearance():
    st = student_record()
    pending = query(
        "SELECT id FROM clearance_requests WHERE student_id = %s AND status = 'pending'",
        (st["id"],),
        fetch="one",
    )
    if request.method == "POST":
        if pending:
            flash("You already have a pending clearance request.", "error")
            return redirect(url_for("student.clearance"))
        
        # Create an empty clearance request and populate all units
        req = query(
            """INSERT INTO clearance_requests (student_id, status)
               VALUES (%s, 'pending') RETURNING id""",
            (st["id"],),
            fetch="one",
        )
        for code, _name in config.CLEARANCE_UNITS:
            query(
                """INSERT INTO clearance_units (request_id, unit_code, status)
                   VALUES (%s, %s, 'pending')""",
                (req["id"], code),
                fetch="none",
            )
        log_action("clearance_started", f"request {req['id']}")
        flash("Clearance request started. You can now upload receipts for each unit.", "success")
        return redirect(url_for("student.request_detail", rid=req["id"]))

    history = query(
        """SELECT * FROM clearance_requests WHERE student_id = %s
           ORDER BY created_at DESC""",
        (st["id"],),
    )
    
    # Fetch units for all history requests to show detailed progress
    for req in history:
        req["units"] = query(
            "SELECT unit_code, status FROM clearance_units WHERE request_id = %s ORDER BY id",
            (req["id"],)
        )

    return render_template(
        "student/clearance.html",
        student=st,
        pending=pending,
        history=history,
    )

@bp.route("/request/<int:rid>", methods=["GET", "POST"])
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
    
    if request.method == "POST":
        unit_id = request.form.get("unit_id")
        unit_record = query("SELECT * FROM clearance_units WHERE id = %s AND request_id = %s", (unit_id, rid), fetch="one")
        if not unit_record:
            flash("Invalid unit.", "error")
            return redirect(url_for("student.request_detail", rid=rid))
        
        rrr = (request.form.get("payment_reference") or "").strip()
        amount = request.form.get("declared_amount") or ""
        file = request.files.get("receipt")
        fee = config.expected_fee(bool(st["is_indigene"]), unit_record["unit_code"])

        if not rrr or len(rrr) < 5:
            flash(f"Payment reference (RRR) is required for {unit_record['unit_code']}.", "error")
            return redirect(url_for("student.request_detail", rid=rid))
        try:
            declared = float(amount)
        except ValueError:
            flash("Enter a valid amount.", "error")
            return redirect(url_for("student.request_detail", rid=rid))
        
        if not file or not file.filename:
            # If they paid online, they might not have a receipt, but let's enforce it for now
            flash("Receipt image is required.", "error")
            return redirect(url_for("student.request_detail", rid=rid))
        
        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED:
            flash("Receipt must be an image (JPG, PNG, GIF, WebP).", "error")
            return redirect(url_for("student.request_detail", rid=rid))

        safe = secure_filename(file.filename)
        stored = f"receipt-{st['id']}-{unit_record['unit_code']}-{safe}"
        dest = config.RECEIPT_DIR / stored
        file.save(dest)

        result = analyze_receipt(st, declared, rrr, str(dest), unit_record["unit_code"])
        
        query(
            """UPDATE clearance_units
               SET receipt_path = %s, receipt_hash = %s, declared_amount = %s,
                   payment_reference = %s, auto_score = %s, auto_decision = %s,
                   auto_reasons = %s, status = 'pending'
               WHERE id = %s""",
            (
                f"/uploads/receipts/{stored}",
                result["file_hash"],
                declared,
                rrr,
                result["score"],
                result["decision"],
                json.dumps(result["reasons"]),
                unit_id
            ),
            fetch="none",
        )
        flash(f"Receipt uploaded for {unit_record['unit_code']} and is now pending review.", "success")
        return redirect(url_for("student.request_detail", rid=rid))

    units = query(
        "SELECT * FROM clearance_units WHERE request_id = %s ORDER BY id",
        (rid,),
    )
    for u in units:
        if u["auto_reasons"]:
            try:
                u["parsed_reasons"] = json.loads(u["auto_reasons"])
            except json.JSONDecodeError:
                u["parsed_reasons"] = [u["auto_reasons"]]
        else:
            u["parsed_reasons"] = []
        u["expected_fee"] = config.expected_fee(bool(st["is_indigene"]), u["unit_code"])

    return render_template(
        "student/request.html",
        req=req,
        units=units,
        student=st,
    )
