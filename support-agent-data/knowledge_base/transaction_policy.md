# Transaction Policy

## Channels supported
- **UPI:** Instant P2P and P2M; 24x7 except maintenance windows.
- **IMPS:** Instant interbank transfer up to INR 5 lakh per transaction (typical retail limit).
- **NEFT:** Batch settlements; available 24x7 with near-hourly batches on most days.
- **RTGS:** High-value transfers; minimum INR 2 lakh; processed in real time during RTGS hours.

## Transaction status definitions
- **Success:** Funds debited/credited as per channel rules; reference number generated.
- **Failed:** No final debit or debit reversed; failure reason code available in app.
- **Pending:** Awaiting confirmation from NPCI, beneficiary bank, or clearing house.
- **Reversed:** Original debit credited back to sender account.

## NEFT and RTGS timelines
- NEFT pending items may take up to 2 hours during peak hours; outside banking hours, next working session.
- RTGS is typically processed within 30 minutes during RTGS operating hours.
- Wrong IFSC or account number may result in rejection or credit to wrong account; recovery requires beneficiary bank coordination.

## Failed transaction analysis
- UPI failures with debit: auto-reversal within 24-48 hours per NPCI guidelines.
- NEFT/IMPS failures: no debit if marked failed; if debited and returned, 1-3 business days.
- Customers should not repeat the same payment until final status is confirmed.

## Duplicate transactions
- Duplicate debits for the same merchant and amount within a short window should be reported with both reference numbers.
- System duplicate detection flags same amount, same beneficiary, within 10 minutes for review.
- Refund of genuine duplicate is processed within 5-7 working days after verification.

## Transaction lookup
- Customers can search by internal transaction ID (TXN reference) or UTR / bank reference number.
- Mini statement shows last 10 transactions; full statement available for download (PDF) for 12 months online.

## Limits and holds
- Large transactions may trigger additional OTP or cooling period for new beneficiaries.
- Regulatory holds on suspicious transactions may delay credit until customer confirmation.

## International remittances
- Outward remittance requires purpose code, PAN, and Form A2 for amounts above thresholds.
- SWIFT transfers take 2-5 business days depending on correspondent banks.
