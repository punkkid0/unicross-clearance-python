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

    # Colors
    navy = HexColor("#1a3a5c")
    gold = HexColor("#c9a227")
    light_blue = HexColor("#eef4fa")
    light_green = HexColor("#e8f5e9")
    green_text = HexColor("#2e7d32")
    text_gray = HexColor("#333333")

    # Double Border
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.rect(20, 20, w - 40, h - 40)
    c.setStrokeColor(navy)
    c.setLineWidth(2)
    c.rect(26, 26, w - 52, h - 52)

    # Header Box (Navy)
    c.setFillColor(navy)
    c.rect(48, h - 170, w - 96, 130, fill=1, stroke=0)
    
    # Header Text (White)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w / 2, h - 70, "UNIVERSITY OF CROSS RIVER STATE")
    c.setFont("Helvetica", 11)
    c.drawCentredString(w / 2, h - 90, "(UNICROSS)")
    
    # Established (Gold)
    c.setFillColor(gold)
    c.setFont("Helvetica", 10)
    c.drawCentredString(w / 2, h - 110, "Established by Edict No. 5 of 2004")
    
    # Department (Gold)
    c.setFont("Helvetica", 9)
    c.drawCentredString(w / 2, h - 150, "BURSARY DEPARTMENT — FINANCE & CLEARANCE OFFICE")

    # Sub-header Banner (Gold)
    c.setFillColor(gold)
    c.rect(48, h - 215, w - 96, 35, fill=1, stroke=0)
    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(w / 2, h - 205, "CLEARANCE CERTIFICATE")

    # Introduction Text
    c.setFillColor(text_gray)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(w / 2, h - 250, "To Whom It May Concern")
    
    c.setFont("Helvetica", 11)
    text1 = "This is to certify that the following student has been duly verified and granted financial"
    text2 = "clearance by the Bursary Department of the University of Cross River State."
    c.drawString(48, h - 280, text1)
    c.drawString(48, h - 300, text2)

    # Details Block (Light Blue)
    c.setFillColor(light_blue)
    c.rect(48, h - 480, w - 96, 150, fill=1, stroke=0)
    
    # Add vertical navy bar on left of details
    c.setFillColor(navy)
    c.rect(48, h - 480, 5, 150, fill=1, stroke=0)

    # Details Text
    c.setFillColor(text_gray)
    
    # Left Column
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(70, h - 360, "FULL NAME")
    c.setFont("Helvetica", 10)
    c.setFillColor(text_gray)
    c.drawString(70, h - 375, student["full_name"])

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(70, h - 410, "USERNAME")
    c.setFont("Helvetica", 10)
    c.setFillColor(text_gray)
    c.drawString(70, h - 425, f"@{student['username']}")

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(70, h - 460, "EMAIL ADDRESS")
    c.setFont("Helvetica", 10)
    c.setFillColor(text_gray)
    c.drawString(70, h - 475, student["email"])

    # Right Column
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(320, h - 360, "REQUEST ID")
    c.setFont("Helvetica", 10)
    c.setFillColor(text_gray)
    c.drawString(320, h - 375, f"#{request_id}")

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(320, h - 410, "CLEARANCE DATE")
    c.setFont("Helvetica", 10)
    c.setFillColor(text_gray)
    c.drawString(320, h - 425, datetime.now().strftime('%d %B %Y'))

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(320, h - 460, "CERTIFICATE NO")
    c.setFont("Helvetica", 10)
    c.setFillColor(text_gray)
    cert_no = f"CERT-{request_id}-{student['id']}F56F6"
    c.drawString(320, h - 475, cert_no)

    # Status Block (Light Green)
    c.setFillColor(light_green)
    c.rect(48, h - 550, w - 96, 50, fill=1, stroke=0)
    
    c.setFillColor(green_text)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(w / 2, h - 520, "CLEARED — No Financial Obligations Outstanding")
    
    c.setFont("Helvetica", 9)
    c.drawCentredString(w / 2, h - 538, "This student has satisfied all financial requirements for the current academic session.")

    # Signatures
    c.setStrokeColor(navy)
    c.setLineWidth(1)
    
    # Left Signature
    c.line(70, h - 650, 250, h - 650)
    c.setFillColor(text_gray)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(70, h - 665, "BURSAR / FINANCE OFFICER")
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(70, h - 677, "University of Cross River State")

    # Right Signature
    c.line(350, h - 650, 520, h - 650)
    c.setFillColor(text_gray)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(350, h - 665, "REGISTRAR")
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(350, h - 677, "University of Cross River State")

    # Footer
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#888888"))
    c.drawCentredString(w / 2, 40, f"Certificate No: {cert_no}  ·  Generated: {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}  ·  Valid only with official university stamp.")

    c.save()
    return f"/uploads/certificates/{filename}"
