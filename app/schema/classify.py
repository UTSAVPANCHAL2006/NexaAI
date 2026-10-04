from typing import Literal
from pydantic import BaseModel, Field


class ClassificationSchema(BaseModel):
    
    category: str = Field(description=" Support category such as account, card, transaction, kyc, dispute, charges, fraud or general.")
    urgency: str = Field(description="Priority level: Low, Medium or High")
    sentiment: str = Field(description="Customer sentiment:Positive , Neutral or Angry")
    action: Literal["retrieve", "call_tool", "clarify", "escalate", "respond"] = Field(description="One of: retrieve, call_tool, clarify, escalate, or respond")
    tool_name: str = Field(description= "Operation to execute. "
            "Examples: get_balance, card_status, block_card, transaction_status, "
            "kyc_status, check_case_status, create_dispute_case, get_user, none.")