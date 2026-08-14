import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from werkzeug.utils import secure_filename
from app.db import query
from app.helpers import login_required, log_action, unit_label
from app.certificate import generate_certificate
import config

bp = Blueprint("admin", __name__, url_prefix="/<admin_type>")

@bp.url_value_preprocessor
def pull_admin_type(endpoint, values):
    if values is not None:
        g.admin_type = values.pop('admin_type', None)

@bp.url_defaults
def add_admin_type(endpoint, values):
    if 'admin_type' not in values:
        if g.get('user'):
            values['admin_type'] = g.user.get('role', 'admin')
        else:
            values['admin_type'] = 'admin'

@bp.route("/dashboard")
@login_required(*config.ADMIN_ROLES)
def dashboard():
    if g.user["role"] == "super_admin":
        stats = {
            "students": query("SELECT COUNT(*) AS n FROM students", fetch="one")["n"],
            "pending": query(
                "SELECT COUNT(*) AS n FROM clearance_requests WHERE status = 'pending'",
                fetch="one",
            )["n"],
            "approved": query(
                "SELECT COUNT(*) AS n FROM clearance_requests WHERE status = 'approved'",
                fetch="one",
            )["n"],
            "payments": query("SELECT COUNT(*) AS n FROM payments WHERE status = 'completed'", fetch="one")["n"],
        }
        recent = query(
            """SELECT cr.*, u.full_name, u.username
               FROM clearance_requests cr
               JOIN students s ON s.id = cr.student_id
               JOIN users u ON u.id = s.user_id
               ORDER BY cr.created_at DESC LIMIT 8"""
        )
    else:
        unit = g.user["role"].replace("admin_", "")
        stats = {
            "students": query("SELECT COUNT(*) AS n FROM students", fetch="one")["n"],
            "pending": query(
                "SELECT COUNT(*) AS n FROM clearance_units WHERE unit_code = %s AND status = 'pending' AND receipt_path IS NOT NULL",
                (unit,), fetch="one"
            )["n"],
            "approved": query(
                "SELECT COUNT(*) AS n FROM clearance_units WHERE unit_code = %s AND status = 'approved'",
                (unit,), fetch="one"
            )["n"],
            "payments": query("SELECT COUNT(*) AS n FROM payments WHERE status = 'completed'", fetch="one")["n"],
        }
        recent = query(
            """SELECT cr.id, cr.student_id, cu.status AS status, cr.created_at, u.full_name, u.username
               FROM clearance_requests cr
               JOIN students s ON s.id = cr.student_id
               JOIN users u ON u.id = s.user_id
               JOIN clearance_units cu ON cu.request_id = cr.id
               WHERE cu.unit_code = %s AND cu.receipt_path IS NOT NULL
               ORDER BY cr.created_at DESC LIMIT 8""",
            (unit,)
        )
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


@bp.route("/requests")
@login_required(*config.ADMIN_ROLES)
def requests():
    status = request.args.get("status") or "all"
    params = []
    if g.user["role"] == "super_admin":
        sql = """SELECT cr.*, u.full_name, u.username, s.matric_no, s.is_indigene
                 FROM clearance_requests cr
                 JOIN students s ON s.id = cr.student_id
                 JOIN users u ON u.id = s.user_id"""
        if status != "all":
            sql += " WHERE cr.status = %s"
            params.append(status)
    else:
        unit = g.user["role"].replace("admin_", "")
        sql = """SELECT cr.*, cu.status AS status, u.full_name, u.username, s.matric_no, s.is_indigene
                 FROM clearance_requests cr
                 JOIN students s ON s.id = cr.student_id
                 JOIN users u ON u.id = s.user_id
                 JOIN clearance_units cu ON cu.request_id = cr.id
                 WHERE cu.unit_code = %s AND cu.receipt_path IS NOT NULL"""
        params.append(unit)
        if status != "all":
            sql += " AND cu.status = %s"
            params.append(status)

    sql += " ORDER BY cr.created_at DESC"
    rows = query(sql, params)
    return render_template("admin/requests.html", rows=rows, status=status)


@bp.route("/requests/<int:rid>", methods=["GET", "POST"])
@login_required(*config.ADMIN_ROLES)
def review(rid):
    req = query(
        """SELECT cr.*, u.full_name, u.username, u.email, s.matric_no, s.is_indigene, s.id AS sid
           FROM clearance_requests cr
           JOIN students s ON s.id = cr.student_id
           JOIN users u ON u.id = s.user_id
           WHERE cr.id = %s""",
        (rid,),
        fetch="one",
    )
    if not req:
        flash("Request not found.", "error")
        return redirect(url_for("admin.requests"))

    if request.method == "POST":
        action = request.form.get("action")
        unit = request.form.get("unit_code")
        reason = (request.form.get("reason") or "").strip()
        role = g.user["role"]

        if action == "indigene":
            if role != "super_admin" and role != "admin_bursary":
                flash("Only Bursary or Super Admin can change indigene status.", "error")
                return redirect(url_for("admin.review", rid=rid))
            flag = request.form.get("is_indigene") == "1"
            query("UPDATE students SET is_indigene = %s WHERE id = %s", (flag, req["sid"]), fetch="none")
            flash("Indigene status updated.", "success")
            return redirect(url_for("admin.review", rid=rid))

        if action in ("approve_unit", "reject_unit"):
            if role != "super_admin" and role != f"admin_{unit}":
                flash(f"You do not have permission to approve/reject the {unit} unit.", "error")
                return redirect(url_for("admin.review", rid=rid))

            if req["status"] != "pending":
                flash("This request is no longer pending.", "error")
                return redirect(url_for("admin.review", rid=rid))
            if action == "reject_unit" and len(reason) < 5:
                flash("Rejection reason must be at least 5 characters.", "error")
                return redirect(url_for("admin.review", rid=rid))
            new_status = "approved" if action == "approve_unit" else "rejected"
            query(
                """UPDATE clearance_units
                   SET status = %s, reason = %s, reviewed_by = %s, reviewed_at = CURRENT_TIMESTAMP
                   WHERE request_id = %s AND unit_code = %s""",
                (new_status, reason or None, g.user["id"], rid, unit),
                fetch="none",
            )
            log_action(f"unit_{new_status}", f"request {rid} unit {unit}")

            if new_status == "rejected":
                query(
                    """UPDATE clearance_requests
                       SET status = 'rejected', updated_at = CURRENT_TIMESTAMP WHERE id = %s""",
                    (rid,),
                    fetch="none",
                )
                flash(f"{unit_label(unit)} rejected the request.", "success")
            else:
                pending_left = query(
                    """SELECT COUNT(*) AS n FROM clearance_units
                       WHERE request_id = %s AND status <> 'approved'""",
                    (rid,),
                    fetch="one",
                )["n"]
                if pending_left == 0:
                    cert = generate_certificate(req, rid)
                    query(
                        """UPDATE clearance_requests
                           SET status = 'approved', certificate_path = %s, updated_at = CURRENT_TIMESTAMP
                           WHERE id = %s""",
                        (cert, rid),
                        fetch="none",
                    )
                    flash("All units approved. Certificate generated.", "success")
                else:
                    flash(f"{unit_label(unit)} approved.", "success")
            return redirect(url_for("admin.review", rid=rid))

    if g.user["role"] == "super_admin":
        units = query(
            "SELECT * FROM clearance_units WHERE request_id = %s ORDER BY id",
            (rid,),
        )
    else:
        unit_code = g.user["role"].replace("admin_", "")
        units = query(
            "SELECT * FROM clearance_units WHERE request_id = %s AND unit_code = %s ORDER BY id",
            (rid, unit_code),
        )
    for u in units:
        if u["auto_reasons"]:
            try:
                u["parsed_reasons"] = json.loads(u["auto_reasons"])
            except json.JSONDecodeError:
                u["parsed_reasons"] = [u["auto_reasons"]]
        else:
            u["parsed_reasons"] = []
    
    return render_template(
        "admin/review.html",
        req=req,
        unit_rows=units,
    )


@bp.route("/ledger", methods=["GET", "POST"])
@login_required(*config.ADMIN_ROLES)
def ledger():
    students = query(
        """SELECT s.id, u.full_name, u.username, s.matric_no, s.is_indigene
           FROM students s JOIN users u ON u.id = s.user_id
           ORDER BY u.full_name"""
    )
    if request.method == "POST":
        rrr = (request.form.get("rrr") or "").strip()
        
        if g.user["role"] == "super_admin":
            payment_type = request.form.get("payment_type")
        else:
            payment_type = g.user["role"].replace("admin_", "")
            
        try:
            student_id = int(request.form.get("student_id"))
            amount = float(request.form.get("amount"))
        except (TypeError, ValueError):
            flash("Select a student and enter a valid amount.", "error")
            return redirect(url_for("admin.ledger"))
        method = request.form.get("payment_method") or "bank_transfer"
        notes = (request.form.get("notes") or "").strip()
        if len(rrr) < 5:
            flash("RRR must be at least 5 characters.", "error")
            return redirect(url_for("admin.ledger"))

        exists = query("SELECT id FROM payments WHERE rrr = %s", (rrr,), fetch="one")
        if exists:
            flash("That RRR is already on the ledger.", "error")
            return redirect(url_for("admin.ledger"))

        query(
            """INSERT INTO payments (rrr, student_id, amount, payment_type, payment_method, status, notes, recorded_by)
               VALUES (%s, %s, %s, %s, %s, 'completed', %s, %s)""",
            (rrr, student_id, amount, payment_type, method, notes or None, g.user["id"]),
            fetch="none",
        )
        log_action("ledger_recorded", rrr)
        flash("Official payment recorded on the ledger.", "success")
        return redirect(url_for("admin.ledger"))

    if g.user["role"] == "super_admin":
        rows = query(
            """SELECT p.*, u.full_name, u.username
               FROM payments p
               JOIN students s ON s.id = p.student_id
               JOIN users u ON u.id = s.user_id
               ORDER BY p.created_at DESC"""
        )
    else:
        unit = g.user["role"].replace("admin_", "")
        rows = query(
            """SELECT p.*, u.full_name, u.username
               FROM payments p
               JOIN students s ON s.id = p.student_id
               JOIN users u ON u.id = s.user_id
               WHERE p.payment_type = %s
               ORDER BY p.created_at DESC""",
            (unit,)
        )
        
    return render_template("admin/ledger.html", students=students, rows=rows, units=config.CLEARANCE_UNITS)


@bp.route("/students", methods=["GET", "POST"])
@login_required(*config.ADMIN_ROLES)
def students():
    if request.method == "POST":
        if g.user["role"] != "super_admin" and g.user["role"] != "admin_bursary":
            flash("Only Bursary or Super Admin can edit student info.", "error")
            return redirect(url_for("admin.students"))
            
        sid = int(request.form.get("student_id"))
        flag = request.form.get("is_indigene") == "1"
        query("UPDATE students SET is_indigene = %s WHERE id = %s", (flag, sid), fetch="none")
        flash("Student updated.", "success")
        return redirect(url_for("admin.students"))
    rows = query(
        """SELECT s.*, u.full_name, u.username, u.email
           FROM students s JOIN users u ON u.id = s.user_id
           ORDER BY u.full_name"""
    )
    return render_template("admin/students.html", rows=rows)


@bp.route("/reports")
@login_required(*config.ADMIN_ROLES)
def reports():
    by_status = query(
        """SELECT status, COUNT(*) AS n FROM clearance_requests GROUP BY status"""
    )
    by_unit = query(
        """SELECT unit_code, status, COUNT(*) AS n
           FROM clearance_units GROUP BY unit_code, status ORDER BY unit_code"""
    )
    payments = query(
        """SELECT COALESCE(SUM(amount),0) AS total, COUNT(*) AS n
           FROM payments WHERE status = 'completed'""",
        fetch="one",
    )
    return render_template(
        "admin/reports.html",
        by_status=by_status,
        by_unit=by_unit,
        payments=payments,
    )

@bp.route("/profile", methods=["GET", "POST"])
@login_required(*config.ADMIN_ROLES)
def profile():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()
        bio = request.form.get("bio", "").strip()

        if not full_name:
            flash("Full name is required.", "error")
            return redirect(url_for("admin.profile"))
            
        profile_pic_path = g.user.get("profile_pic_path")
        credentials_path = g.user.get("credentials_path")

        ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
        
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

        cred_file = request.files.get("credentials")
        if cred_file and cred_file.filename:
            ext = "." + cred_file.filename.rsplit(".", 1)[-1].lower() if "." in cred_file.filename else ""
            if ext in ALLOWED_EXTS:
                safe = secure_filename(cred_file.filename)
                stored = f"cred-{g.user['id']}-{safe}"
                dest = config.CREDENTIALS_DIR / stored
                cred_file.save(dest)
                credentials_path = f"/uploads/credentials/{stored}"
            else:
                flash("Credentials must be an image or PDF.", "error")

        query(
            """UPDATE users SET full_name = %s, phone = %s, bio = %s, 
               profile_pic_path = %s, credentials_path = %s WHERE id = %s""",
            (full_name, phone, bio, profile_pic_path, credentials_path, g.user["id"]),
            fetch="none"
        )
        flash("Profile updated successfully.", "success")
        return redirect(url_for("admin.profile"))

    return render_template("admin/profile.html")
