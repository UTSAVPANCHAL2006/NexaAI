from app.common.logger import get_logger
from app.common.custom_exception import CustomException

from app.rag.llm import LLM

logger = get_logger(__name__)

from app.prompts.generate_prompt import GENERATE_PROMPT

class Generator:

    def __init__(self, llm):
        self.llm = llm

    def generate(
        self,
        ticket: str,
        action: str,
        documents=None,
        tool_result=None,
        history=None,
        account_id=None,
        case_id=None,
        card_last4=None,
        txn_id=None,
    ):
        if history is None:
            history = []

        if documents:
            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )
        else:
            context = "No documents."

        if tool_result is None:
            tool_result = {}

        chain = GENERATE_PROMPT | self.llm

        payload = {
            "ticket": ticket,
            "action": action,
            "documents": context,
            "tool_result": str(tool_result),
            "history": history,
            "account_id": str(account_id) if account_id else "None",
            "case_id": str(case_id) if case_id else "None",
            "card_last4": str(card_last4) if card_last4 else "None",
            "txn_id": str(txn_id) if txn_id else "None"
        }

        response = chain.invoke(payload)

        return response
        
    def stream_generate(
        self,
        ticket: str,
        action: str,
        documents=None,
        tool_result=None,
        history=None,
        account_id=None,
        case_id=None,
        card_last4=None,
        txn_id=None,
    ):
        if history is None:
            history = []

        if documents:
            context = "\n\n".join(doc.page_content for doc in documents)
        else:
            context = "No documents."

        if tool_result is None:
            tool_result = {}

        chain = GENERATE_PROMPT | self.llm

        payload = {
            "ticket": ticket,
            "action": action,
            "documents": context,
            "tool_result": str(tool_result),
            "history": history,
            "account_id": str(account_id) if account_id else "None",
            "case_id": str(case_id) if case_id else "None",
            "card_last4": str(card_last4) if card_last4 else "None",
            "txn_id": str(txn_id) if txn_id else "None"
        }

        for chunk in chain.stream(payload):
            yield chunk.content
