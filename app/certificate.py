from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
import config


def generate_certificate(student, request_id: int) -> str:
    config.CERT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"clearance-{request_id}.pdf"
    path = config.CERT_DIR / filename

    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    navy = HexColor("#1a3a5c")
    gold = HexColor("#c9a227")

    c.setStrokeColor(navy)
    c.setLineWidth(3)
    c.rect(24, 24, w - 48, h - 48)
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.rect(32, 32, w - 64, h - 64)

    c.setFillColor(navy)
    c.rect(48, h - 150, w - 96, 100, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Times-Bold", 16)
    c.drawCentredString(w / 2, h - 90, "UNIVERSITY OF CROSS RIVER STATE")
    c.setFont("Times-Roman", 11)
    c.drawCentredString(w / 2, h - 110, "(UNICROSS)")
    c.setFillColor(gold)
    c.setFont("Times-Roman", 9)
    c.drawCentredString(w / 2, h - 130, "BURSARY DEPARTMENT — CLEARANCE OFFICE")

    c.setFillColor(gold)
    c.rect(48, h - 195, w - 96, 32, fill=1, stroke=0)
    c.setFillColor(navy)
    c.setFont("Times-Bold", 14)
    c.drawCentredString(w / 2, h - 185, "CLEARANCE CERTIFICATE")

    c.setFillColor(HexColor("#222222"))
    c.setFont("Times-Roman", 12)
    y = h - 250
    lines = [
        "To Whom It May Concern",
        "",
        f"This is to certify that {student['full_name']}",
        f"(Username: {student['username']}, Matric: {student.get('matric_no') or 'N/A'})",
        "has fulfilled the required school-fee payment and has been",
        "cleared by the relevant university units.",
        "",
        f"Certificate generated: {datetime.now().strftime('%d %B %Y')}",
        f"Request reference: #{request_id}",
    ]
    for line in lines:
        c.drawCentredString(w / 2, y, line)
        y -= 20

    c.setFont("Times-Italic", 9)
    c.setFillColor(HexColor("#666666"))
    c.drawCentredString(w / 2, 60, "UNICROSS — Bursary Department, Cross River State, Nigeria")
    c.save()
    return f"/uploads/certificates/{filename}"
