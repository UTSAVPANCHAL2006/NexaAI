# UPI Transaction Policy

## Overview
Unified Payments Interface (UPI) enables instant fund transfers between bank accounts using a virtual payment address (VPA) or QR code. Transactions are processed through NPCI rails and are subject to daily limits and device binding rules.

## Successful payments
- Successful UPI payments are usually instant and reflected in the beneficiary account within seconds.
- Once marked successful, reversal depends on the merchant or beneficiary; the bank cannot unilaterally reverse without a dispute or beneficiary consent.
- Customers should save the UTR / UPI reference number shown in the transaction receipt.

## Failed payments
- Failed UPI attempts should not debit the account; if debited, the amount is typically auto-reversed within 24-48 hours.
- Common failure reasons include: insufficient balance, wrong UPI PIN, beneficiary bank downtime, NPCI timeout, daily limit exceeded, or device not registered.
- Customers should wait at least 30 minutes before retrying the same payment to avoid duplicate debits.

## Pending status
- A pending UPI status may appear for up to 48 hours during network congestion; check status using UTR or transaction reference in the mobile app.
- If pending beyond 48 hours, raise a service request with transaction date, amount, and UTR.

## Limits
- Default per-transaction UPI limit for retail savings accounts: INR 1,00,000 (may vary by customer profile and bank policy).
- Daily UPI transfer limit applies across all UPI apps linked to the same account.
- Newly registered UPI users may have a lower limit for the first 24 hours after activation.

## Complaints and disputes
- For unauthorized UPI debits, block the UPI ID / deregister suspicious apps and report within 24 hours for faster dispute handling.
- Merchant non-refund disputes require transaction proof; investigation SLA is typically 7-15 working days.

## Customer responsibilities
- Do not share UPI PIN or OTP with anyone.
- Verify beneficiary name on the confirmation screen before entering PIN.
- Use official bank apps only; avoid unknown QR codes for payments.
