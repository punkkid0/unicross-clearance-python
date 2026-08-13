# UNICROSS Payment Verification & Clearance System (Python)

Web application for **University of Cross River State** school-fee verification and student clearance.

This is the version that matches **Chapter 3.6** of the project write-up:

| Thesis tool | This project |
|---|---|
| Frontend: HTML, CSS, JavaScript | `templates/` + `static/css` + `static/js` |
| Backend: PHP / **Python** / Java | **Python 3 + Flask** |
| Database: MySQL or **PostgreSQL** | **PostgreSQL** |
| Modeling: Draw.io / Lucidchart | `diagrams/` |
| Payment: bank APIs / gateways | Official ledger + optional **Paystack** |

The older Node.js / React project is **not** this repo. Keep that folder only as backup.

## What it does

- Students register, pay (or use a bursary-recorded RRR), upload a receipt, and track clearance.
- The server checks the RRR against the official ledger and the indigene / non-indigene fee (₦75,600 / ₦81,500).
- Six units from the thesis can approve: **Bursary, Library, Faculty, Department, Hostel, Student Affairs**.
- When all six approve, a PDF clearance certificate is generated.
- Admins record ledger payments, set indigene status, review requests, and view reports.

## Install on Windows

Read **[INSTALL.md](INSTALL.md)**, then:

1. Double-click `setup.bat`
2. Double-click `start.bat`
3. Open http://localhost:5000

## Demo logins

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Student | `student1` | `student123` |

`student1` is an indigene. Demo RRR: `RRR-STUDENT1-001234567890` (₦75,600).

## How to try the flow

1. Log in as **admin** → **Ledger** (confirm the demo RRR, or record a new one).
2. Log in as **student1** → **Request Clearance** → upload any image → amount `75600` → that RRR.
3. As **admin**, open the request and **approve each unit**.
4. As the student, download the certificate.

## Optional Paystack

Put test keys in `.env`:

```
PAYSTACK_SECRET_KEY=sk_test_...
PAYSTACK_PUBLIC_KEY=pk_test_...
```

Then **Pay Fees** starts a real Paystack test checkout. A successful pay writes the official ledger automatically.

Without keys, bursary records the payment on the ledger (allowed by the write-up when a live API is not available).
