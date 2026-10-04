import re

from app.agents.state import Agentstate
from app.agents.session_context import format_session_context
from app.prompts.entity_prompt import ENTITY_PROMPT
from app.schema.entity import EntitySchema
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

USER_ID_PATTERN = re.compile(r"\b(user_\d+)\b", re.IGNORECASE)
BANKING_ID_PATTERN = re.compile(
    r"\b((?:ACC|CRD|TXN|CASE)-\d+)\b", re.IGNORECASE
)
CARD_LAST4_PATTERN = re.compile(r"\b(\d{4})\b")


class EntityExtractorNode:
    
    def __init__(self, llm):
        self.llm = llm
        
    def entity_extractor_node(self, state: Agentstate):
        try:
            logger.info("EntityExtractorNode started")
            structured_llm = self.llm.with_structured_output(
                EntitySchema, method="json_schema"
            )

            chain = ENTITY_PROMPT | structured_llm

            result = chain.invoke({
                "ticket": state["ticket"],
                "session_context": format_session_context(state),
                "history": state.get("messages", [])[-4:],
            })

            updates = {}
            ticket = state["ticket"]

            account_id = result.account_id
            if not account_id:
                m = BANKING_ID_PATTERN.search(ticket)
                if m:
                    account_id = m.group(1).upper()
            if account_id:
                updates["account_id"] = str(account_id).strip().upper()

            if result.case_id:
                updates["case_id"] = str(result.case_id).strip().upper()

            user_id = result.user_id
            if not user_id:
                m = USER_ID_PATTERN.search(ticket)
                if m:
                    user_id = m.group(1).lower()
            if user_id:
                updates["user_id"] = str(user_id).strip().lower()

            card_last4 = result.card_last4
            if not card_last4:
                stripped = ticket.strip()
                if CARD_LAST4_PATTERN.fullmatch(stripped):
                    card_last4 = stripped
                elif re.search(r"last\s*4|last\s*four|ending\s*in", ticket, re.I):
                    matches = list(CARD_LAST4_PATTERN.finditer(ticket))
                    if matches:
                        card_last4 = matches[-1].group(1)
            if card_last4:
                updates["card_last4"] = str(card_last4).strip()

            if result.txn_id:
                updates["txn_id"] = str(result.txn_id).strip().upper()
                
            logger.info(f"EntityExtractorNode result: extracted {list(updates.keys())}")
            return updates
            
        except Exception as e:
            logger.error(f"Error in EntityExtractorNode: {str(e)}")
            raise CustomException(f"EntityExtractorNode Failed", e)
