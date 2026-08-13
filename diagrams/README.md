# Thesis diagrams (Chapter 3)

Open [diagrams.drawio](https://app.diagrams.net/) and recreate these from the running system. Export PNG into this folder for Chapter 3.

| Figure | Content |
|---|---|
| 3.1 Flowchart | Student login → enter payment / upload receipt → gateway or ledger check → admin units approve or reject → status update |
| 3.2 Three-tier | Browser (HTML/CSS/JS) → Flask application layer → PostgreSQL |
| 3.3 Use case | Student: register, login, pay, upload receipt, track status. Admin: verify payment, approve units, reports, manage students |
| 3.4 ER | users, students, departments, school_fee_payments, payments, transactions, clearance_requests, clearance_units |
| 3.5 Workflow | Pay → verify → store → officers review → digital clearance → student notified |

The live software already implements this flow. These drawings are for the printed chapter, as required by section 3.6 item 4.
