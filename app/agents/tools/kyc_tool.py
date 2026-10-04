import json
from app.config.config import KYC_PATH

class KycTool:

    def __init__(self):
        with open(KYC_PATH, "r") as f:
            self.kyc_records = json.load(f)

    def kyc_status(self, user_id: str):
        if not user_id or not str(user_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your customer ID (e.g. user_7) to check KYC status.",
            }
        user_id = user_id.strip()
        record = self.kyc_records.get(user_id)
        if record is None:
            return {
                "success": False,
                "message": "KYC record not found for this customer.",
            }
        return {
            "success": True,
            "user_id": user_id,
            "kyc": record,
        }

    def missing_kyc_documents(self, user_id: str):
        result = self.kyc_status(user_id)
        if not result.get("success"):
            return result
        missing = result["kyc"].get("missing_documents", [])
        return {
            "success": True,
            "user_id": user_id,
            "missing_documents": missing,
            "message": "No missing documents." if not missing else "Please submit the listed documents.",
        }

    def kyc_verification_status(self, user_id: str):
        result = self.kyc_status(user_id)
        if not result.get("success"):
            return result
        kyc = result["kyc"]
        return {
            "success": True,
            "user_id": user_id,
            "kyc_status": kyc.get("kyc_status"),
            "pan_verified": kyc.get("pan_verified"),
            "aadhaar_verified": kyc.get("aadhaar_verified"),
            "tier": kyc.get("tier"),
        }
