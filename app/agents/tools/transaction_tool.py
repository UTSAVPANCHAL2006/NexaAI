import json
from app.config.config import TRANSACTIONS_PATH

class TransactionTool:

    def __init__(self):
        with open(TRANSACTIONS_PATH, "r") as f:
            self.transactions = json.load(f)

    def by_txn_id(self, txn_id: str):
        txn_id = txn_id.strip().upper()
        txn = self.transactions.get(txn_id)
        if txn is None:
            return None, None
        row = txn.copy()
        row["txn_id"] = txn_id
        return txn_id, row

    def by_utr(self, utr: str):
        utr = utr.strip().upper()
        for txn_id, txn in self.transactions.items():
            if str(txn.get("utr", "")).upper() == utr:
                row = txn.copy()
                row["txn_id"] = txn_id
                return txn_id, row
        return None, None

    def transaction_lookup(self, txn_id: str = None, utr: str = None):
        if txn_id:
            found_id, row = self.by_txn_id(txn_id)
            if row:
                return {"success": True, "transaction": row}
        if utr:
            found_id, row = self.by_utr(utr)
            if row:
                return {"success": True, "transaction": row}
        return {
            "success": False,
            "needs_clarification": True,
            "message": "Please share transaction ID (e.g. TXN-9001) or UTR reference.",
        }

    def transaction_status(self, txn_id: str = None, utr: str = None):
        result = self.transaction_lookup(txn_id=txn_id, utr=utr)
        if not result.get("success"):
            return result
        txn = result["transaction"]
        return {
            "success": True,
            "txn_id": txn.get("txn_id"),
            "status": txn.get("status"),
            "channel": txn.get("channel"),
            "amount": txn.get("amount"),
            "currency": txn.get("currency"),
        }

    def failed_transaction(self, txn_id: str = None, utr: str = None):
        result = self.transaction_lookup(txn_id=txn_id, utr=utr)
        if not result.get("success"):
            return result
        txn = result["transaction"]
        if txn.get("status") != "failed":
            return {
                "success": True,
                "message": "This transaction is not in failed status.",
                "transaction": txn,
            }
        return {
            "success": True,
            "transaction": txn,
            "failure_reason": txn.get("failure_reason", "Unknown"),
            "analysis": "Retry after 30 minutes if balance was debited; otherwise no debit should occur per UPI policy.",
        }

    def pending_transaction(self, txn_id: str = None, utr: str = None):
        result = self.transaction_lookup(txn_id=txn_id, utr=utr)
        if not result.get("success"):
            return result
        txn = result["transaction"]
        if txn.get("status") != "pending":
            return {
                "success": True,
                "message": "This transaction is not pending.",
                "transaction": txn,
            }
        return {
            "success": True,
            "transaction": txn,
            "note": "NEFT pending items may take up to 2 hours during banking hours.",
        }

    def duplicate_transaction(self, txn_id: str = None, utr: str = None):
        result = self.transaction_lookup(txn_id=txn_id, utr=utr)
        if not result.get("success"):
            return result
        txn = result["transaction"]
        amount = txn.get("amount")
        account_id = txn.get("account_id")
        duplicates = []
        for other_id, other in self.transactions.items():
            if other_id == txn.get("txn_id"):
                continue
            if other.get("account_id") == account_id and other.get("amount") == amount:
                if other.get("status") == "success":
                    dup = other.copy()
                    dup["txn_id"] = other_id
                    duplicates.append(dup)
        return {
            "success": True,
            "reference_transaction": txn,
            "possible_duplicates": duplicates,
            "duplicate_detected": len(duplicates) > 0,
        }
