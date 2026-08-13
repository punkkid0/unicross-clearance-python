import uuid
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from app.db import query
from app.helpers import login_required, student_record, log_action
import config

bp = Blueprint("pay", __name__, url_prefix="/pay")


@bp.route("/", methods=["GET", "POST"])
@login_required("student")
def start():
    st = student_record()
    fee = config.expected_fee(bool(st["is_indigene"]))
    if request.method == "POST":
        if not config.PAYSTACK_SECRET_KEY:
            flash(
                "Online gateway is not configured. Ask bursary to record your payment on the official ledger, then submit clearance with your RRR.",
                "error",
            )
            return redirect(url_for("student.clearance"))
        ref = f"PSK-{st['id']}-{uuid.uuid4().hex[:10]}"
        query(
            """INSERT INTO transactions (student_id, provider, reference, amount, status)
               VALUES (%s, 'paystack', %s, %s, 'initialized')""",
            (st["id"], ref, fee),
            fetch="none",
        )
        payload = {
            "email": st["email"],
            "amount": int(fee * 100),
            "reference": ref,
            "callback_url": f"{config.BASE_URL}/pay/callback",
            "metadata": {"student_id": st["id"]},
        }
        headers = {"Authorization": f"Bearer {config.PAYSTACK_SECRET_KEY}"}
        try:
            res = requests.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers=headers,
                timeout=20,
            )
            data = res.json()
        except requests.RequestException as exc:
            flash(f"Could not reach Paystack: {exc}", "error")
            return redirect(url_for("pay.start"))
        if not data.get("status"):
            flash(data.get("message") or "Paystack did not start the payment.", "error")
            return redirect(url_for("pay.start"))
        return redirect(data["data"]["authorization_url"])
    return render_template("student/pay.html", student=st, fee=fee)


@bp.route("/callback")
@login_required("student")
def callback():
    st = student_record()
    ref = request.args.get("reference") or request.args.get("trxref")
    if not ref:
        flash("Missing payment reference.", "error")
        return redirect(url_for("student.dashboard"))
    if not config.PAYSTACK_SECRET_KEY:
        flash("Gateway is not configured.", "error")
        return redirect(url_for("student.dashboard"))
    headers = {"Authorization": f"Bearer {config.PAYSTACK_SECRET_KEY}"}
    res = requests.get(
        f"https://api.paystack.co/transaction/verify/{ref}",
        headers=headers,
        timeout=20,
    )
    data = res.json()
    if not data.get("status") or data.get("data", {}).get("status") != "success":
        query(
            "UPDATE transactions SET status = 'failed' WHERE reference = %s",
            (ref,),
            fetch="none",
        )
        flash("Payment was not successful.", "error")
        return redirect(url_for("pay.start"))

    amount = data["data"]["amount"] / 100.0
    query(
        "UPDATE transactions SET status = 'success' WHERE reference = %s",
        (ref,),
        fetch="none",
    )
    existing = query(
        "SELECT id FROM school_fee_payments WHERE rrr = %s",
        (ref,),
        fetch="one",
    )
    if not existing:
        query(
            """INSERT INTO school_fee_payments
               (rrr, student_id, amount, payment_method, status, gateway_ref, notes)
               VALUES (%s, %s, %s, 'paystack', 'successful', %s, 'Paystack verified')""",
            (ref, st["id"], amount, ref),
            fetch="none",
        )
        query(
            """INSERT INTO payments (student_id, amount, payment_type, status, rrr)
               VALUES (%s, %s, 'school_fee', 'completed', %s)""",
            (st["id"], amount, ref),
            fetch="none",
        )
    log_action("paystack_verified", ref)
    flash(f"Payment confirmed. Your RRR is {ref}. You can now submit clearance.", "success")
    return redirect(url_for("student.clearance"))
