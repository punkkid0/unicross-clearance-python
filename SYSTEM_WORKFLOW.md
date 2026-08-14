# UNICROSS Clearance System Workflow Guide

This document explains the core mechanics of the clearance system, specifically focusing on how the Payment Ledger and Auto-Check system work. It also provides the exact workflows to use during the project defense.

---

## 1. The Official Payment Ledger (Source of Truth)
Because this thesis project operates without a live, real-time connection to a real bank API (like Remita or Paystack), the system relies on the **Official Payment Ledger** to verify transactions.

**How it works in the real world:**
1. A student goes to the bank, pays their fee (e.g., School Fees), and receives a physical teller with a unique **RRR number**.
2. The student takes that physical teller to the Bursary.
3. The Bursary Admin logs into the system, navigates to the **Ledger** page, and manually records that the student paid the fee using that specific RRR.
4. The database now definitively knows that the money is in the school's account.

---

## 2. The Auto-Check System
When a student logs into their dashboard to request clearance, they must upload a picture of their receipt and type in their RRR. The moment they hit "Submit", an automated script runs in the background to grade the receipt out of 100 points. 

The Auto-Check verifies three things:
1. **Duplicate Image Check:** It uses a cryptographic hash (`SHA-256`) to mathematically scan the uploaded image. If another student has already uploaded that exact same picture, the system instantly flags it as a duplicate (prevents forgery).
2. **Amount Check:** It checks if the student's declared amount matches the exact fee required for their department and indigene status (e.g., exactly ₦81,500).
3. **RRR Verification:** It checks the RRR against the database. 

### How RRR Verification handles different scenarios:
- **Ledger Match:** If the auto-check finds the RRR in the Bursary Ledger, and the amount matches, it scores it high (Authentic - 90/100).
- **Wrong Department:** RRRs are unique per fee. If a student tries to use a valid Bursary RRR to clear their Library fee, the auto-check will flag it as "Not Found" because it specifically looks for a Library payment.
- **Underpaid:** If the RRR is in the ledger, but the ledger says they only paid ₦500 instead of ₦81,500, the auto-check flags it as suspicious.

---

## 3. Defense Demonstration Workflows

During your project defense, you have two distinct ways to present the system to your supervisor:

### Method A: The "Automated API" Simulation (Fastest)
To prove that the system is built to handle modern API integrations, a secret "simulation" code has been added to the auto-checker.
- **The Demo:** Log in as a student, upload a receipt, and type an RRR that starts with exactly `RRR-SIM-` (for example, `RRR-SIM-12345`).
- **The Result:** The system will bypass the ledger entirely, pretend it successfully talked to the bank's API, and score it **98/100** ("VERIFIED: payment confirmed dynamically via API"). This is perfect for quickly clearing test students during the presentation!

### Method B: The "Manual Verification" Backup (Thorough)
If the supervisor asks what happens if the API is down or if a student uses a physical bank draft, use this method.
- **The Demo:** 
  1. Act as the Bursary Admin. Go to the Ledger and manually record a payment for a student (e.g., RRR: `BANK-001`).
  2. Switch to the Student account. Upload a receipt and type in `BANK-001`.
  3. Switch to the Admin account. Go to the Review page. The auto-check will show that the receipt is Authentic because it successfully cross-referenced the RRR with the manual ledger!
