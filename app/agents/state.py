from typing import TypedDict , Annotated
from langchain_core.documents import Document
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class Agentstate(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    ticket : str
    category : str
    urgency : str
    sentiment : str
    action : str  
    tool_name : str
    documents : list[Document]
    tool_result: dict
    response : str
    account_id: str | None
    case_id: str | None
    user_id: str | None
    card_last4: str | None
    txn_id: str | None
