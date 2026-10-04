from typing import Optional
from pydantic import BaseModel, Field

class EntitySchema(BaseModel):
    
    case_id : Optional[str] = Field(default=None,description="Case ID (CASE-XXXX) if present, otherwise null")
    account_id : Optional[str] = Field(default=None,description="Account ID (ACC-XXXX) or Card ID (CRD-XXXX) if present, otherwise null")
    user_id : Optional[str] = Field(default=None,description="Customer ID if present, otherwise null")
    card_last4 : Optional[str] = Field(default=None,description="Card last 4 digits if present, otherwise null")
    txn_id : Optional[str] = Field(default=None,description="Transaction ID (TXN-XXXX) or UTR if present, otherwise null")
