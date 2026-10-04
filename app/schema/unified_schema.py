from typing import Literal, Optional
from pydantic import BaseModel, Field


class UnifiedClassificationSchema(BaseModel):
    category: str = Field(description="Support category: account, card, transaction, kyc, dispute, charges, fraud, general")
    urgency: str = Field(description="Priority: low, medium, high")
    sentiment: str = Field(description="Customer sentiment: positive, neutral, negative")
    action: Literal["retrieve", "call_tool", "clarify", "escalate", "respond"] = Field(description="One of: retrieve, call_tool, clarify, escalate, respond")
    tool_name: str = Field(description="Tool name: get_balance, card_status, block_card, transaction_status, failed_transaction, kyc_status, check_case_status, create_dispute_case, get_user, none")
    
    # Entity extraction
    case_id: Optional[str] = Field(default=None, description="Case ID (CASE-XXXX) if present, otherwise null")
    account_id: Optional[str] = Field(default=None, description="Account ID (ACC-XXXX) or Card ID (CRD-XXXX) if present, otherwise null")
    user_id: Optional[str] = Field(default=None, description="Customer ID (user_X) if present, otherwise null")
    card_last4: Optional[str] = Field(default=None, description="Card last 4 digits (e.g. 4521) if present, otherwise null")
    txn_id: Optional[str] = Field(default=None, description="Transaction ID (TXN-XXXX) or UTR if present, otherwise null")
