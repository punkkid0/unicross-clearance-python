import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.db import query
from app.helpers import login_required, log_action, unit_label
from app.certificate import generate_certificate
import config

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard")
@login_required("admin")
def dashboard():
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
        "payments": query("SELECT COUNT(*) AS n FROM school_fee_payments", fetch="one")["n"],
    }
    recent = query(
        """SELECT cr.*, u.full_name, u.username
           FROM clearance_requests cr
           JOIN students s ON s.id = cr.student_id
           JOIN users u ON u.id = s.user_id
           ORDER BY cr.created_at DESC LIMIT 8"""
    )
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


@bp.route("/requests")
@login_required("admin")
def requests():
    status = request.args.get("status") or "all"
    sql = """SELECT cr.*, u.full_name, u.username, s.matric_no, s.is_indigene
             FROM clearance_requests cr
             JOIN students s ON s.id = cr.student_id
             JOIN users u ON u.id = s.user_id"""
    params = []
    if status != "all":
        sql += " WHERE cr.status = %s"
        params.append(status)
    sql += " ORDER BY cr.created_at DESC"
    rows = query(sql, params)
    return render_template("admin/requests.html", rows=rows, status=status)


@bp.route("/requests/<int:rid>", methods=["GET", "POST"])
@login_required("admin")
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

        if action == "indigene":
            flag = request.form.get("is_indigene") == "1"
            query("UPDATE students SET is_indigene = %s WHERE id = %s", (flag, req["sid"]), fetch="none")
            flash("Indigene status updated.", "success")
            return redirect(url_for("admin.review", rid=rid))

        if action in ("approve_unit", "reject_unit"):
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
    fee = config.expected_fee(bool(req["is_indigene"]))
    return render_template(
        "admin/review.html",
        req=req,
        units=units,
        reasons=reasons,
        fee=fee,
    )


@bp.route("/ledger", methods=["GET", "POST"])
@login_required("admin")
def ledger():
    students = query(
        """SELECT s.id, u.full_name, u.username, s.matric_no, s.is_indigene
           FROM students s JOIN users u ON u.id = s.user_id
           ORDER BY u.full_name"""
    )
    if request.method == "POST":
        rrr = (request.form.get("rrr") or "").strip()
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
        if amount not in (config.FEE_INDIGENE, config.FEE_NON_INDIGENE):
            flash("Amount must be the official indigene or non-indigene fee.", "error")
            return redirect(url_for("admin.ledger"))
        exists = query("SELECT id FROM school_fee_payments WHERE rrr = %s", (rrr,), fetch="one")
        if exists:
            flash("That RRR is already on the ledger.", "error")
            return redirect(url_for("admin.ledger"))
        query(
            """INSERT INTO school_fee_payments
               (rrr, student_id, amount, payment_method, notes, recorded_by)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (rrr, student_id, amount, method, notes or None, g.user["id"]),
            fetch="none",
        )
        query(
            """INSERT INTO payments (student_id, amount, payment_type, status, rrr)
               VALUES (%s, %s, 'school_fee', 'completed', %s)""",
            (student_id, amount, rrr),
            fetch="none",
        )
        log_action("ledger_recorded", rrr)
        flash("Official payment recorded on the ledger.", "success")
        return redirect(url_for("admin.ledger"))

    rows = query(
        """SELECT p.*, u.full_name, u.username
           FROM school_fee_payments p
           JOIN students s ON s.id = p.student_id
           JOIN users u ON u.id = s.user_id
           ORDER BY p.payment_date DESC"""
    )
    return render_template("admin/ledger.html", students=students, rows=rows)


@bp.route("/students", methods=["GET", "POST"])
@login_required("admin")
def students():
    if request.method == "POST":
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
@login_required("admin")
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
           FROM school_fee_payments WHERE status = 'successful'""",
        fetch="one",
    )
    return render_template(
        "admin/reports.html",
        by_status=by_status,
        by_unit=by_unit,
        payments=payments,
    )
