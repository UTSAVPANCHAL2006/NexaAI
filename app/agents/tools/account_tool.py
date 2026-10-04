import json
from app.config.config import ACCOUNTS_PATH, TRANSACTIONS_PATH

class AccountTool:

    def __init__(self):
        with open(ACCOUNTS_PATH, "r") as f:
            self.accounts = json.load(f)

        with open(TRANSACTIONS_PATH, "r") as f:
            self.transactions = json.load(f)

    def get_balance(self, account_id: str):
        if not account_id or not str(account_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your account ID (e.g. ACC-1001).",
            }
        account_id = account_id.strip().upper()
        account = self.accounts.get(account_id)
        if account is None:
            return {
                "success": False,
                "message": "Account not found.",
            }
        return {
            "success": True,
            "account_id": account_id,
            "balance": account["balance"],
            "currency": account["currency"],
            "status": account["status"],
        }

    def get_account_details(self, account_id: str):
        if not account_id or not str(account_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your account ID (e.g. ACC-1001).",
            }
        account_id = account_id.strip().upper()
        account = self.accounts.get(account_id)
        if account is None:
            return {
                "success": False,
                "message": "Account not found.",
            }
        account_copy = account.copy()
        account_copy["account_id"] = account_id
        return {
            "success": True,
            "account": account_copy,
        }

    def recent_transactions(self, account_id: str, limit: int = 5):
        if not account_id or not str(account_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your account ID (e.g. ACC-1001).",
            }
        account_id = account_id.strip().upper()
        if account_id not in self.accounts:
            return {
                "success": False,
                "message": "Account not found.",
            }
        txns = []
        for txn_id, txn in self.transactions.items():
            if txn.get("account_id") == account_id:
                row = txn.copy()
                row["txn_id"] = txn_id
                txns.append(row)
        txns.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return {
            "success": True,
            "account_id": account_id,
            "transactions": txns[:limit],
        }

    def spending_summary(self, account_id: str):
        if not account_id or not str(account_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your account ID (e.g. ACC-1001).",
            }
        account_id = account_id.strip().upper()
        if account_id not in self.accounts:
            return {
                "success": False,
                "message": "Account not found.",
            }
        total_success = 0.0
        count_success = 0
        total_failed = 0.0
        for txn in self.transactions.values():
            if txn.get("account_id") != account_id:
                continue
            if txn.get("status") == "success":
                total_success += float(txn.get("amount", 0))
                count_success += 1
            elif txn.get("status") == "failed":
                total_failed += float(txn.get("amount", 0))
        return {
            "success": True,
            "account_id": account_id,
            "successful_spend": total_success,
            "failed_attempts_amount": total_failed,
            "successful_transaction_count": count_success,
            "currency": self.accounts[account_id]["currency"],
        }
