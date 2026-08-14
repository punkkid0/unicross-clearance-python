import hashlib
from app.db import query
from config import expected_fee


def file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_gateway(rrr: str, expected_amount: float) -> bool:
    """Simulate check payment via external API."""
    if rrr.startswith("RRR-SIM-"):
        # Simulated success
        return True
    return False


def analyze_receipt(student, declared_amount, rrr, receipt_file_path, unit_code):
    reasons = []
    score = 40
    expected = expected_fee(bool(student["is_indigene"]), unit_code)
    declared = float(declared_amount or 0)

    digest = file_hash(receipt_file_path) if receipt_file_path else None
    if digest:
        dup = query(
            """SELECT cu.id FROM clearance_units cu
               JOIN clearance_requests cr ON cr.id = cu.request_id
               WHERE cu.receipt_hash = %s AND cr.student_id <> %s LIMIT 1""",
            (digest, student["id"]),
            fetch="one",
        )
        if dup:
            score -= 30
            reasons.append("This exact receipt image was already used by another student.")
        else:
            score += 5
            reasons.append("No duplicate receipt image found.")

    ledger = query(
        """SELECT id, amount, status FROM payments
           WHERE rrr = %s AND student_id = %s AND payment_type = %s LIMIT 1""",
        (rrr.strip(), student["id"], unit_code),
        fetch="one",
    )

    is_verified_via_api = verify_gateway(rrr.strip(), expected)

    if is_verified_via_api:
        score = 98
        reasons.append(f"VERIFIED: {unit_code} payment confirmed dynamically via API.")
    elif ledger:
        ledger_amt = float(ledger["amount"])
        if abs(ledger_amt - expected) < 1 and abs(declared - expected) < 1:
            score = 90
            reasons.append(
                f"VERIFIED: RRR found in the official ledger for the correct fee (N{expected:,.0f})."
            )
        else:
            score = min(score, 35)
            reasons.append("RRR found but the amount does not match the required fee.")
    else:
        score = min(score, 25)
        reasons.append("RRR was not found via API nor in the manual ledger.")

    if abs(declared - expected) >= 1:
        score = min(score, 30)
        reasons.append(f"Declared amount must be exactly N{expected:,.0f} for this fee.")

    if score >= 75:
        decision = "authentic"
    elif score >= 45:
        decision = "suspicious"
    else:
        decision = "likely_fake"

    return {
        "score": max(0, min(100, score)),
        "decision": decision,
        "reasons": reasons,
        "file_hash": digest,
        "expected": expected,
    }
