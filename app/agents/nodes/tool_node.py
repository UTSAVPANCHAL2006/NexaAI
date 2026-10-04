from app.agents.state import Agentstate
from app.agents.tools.account_tool import AccountTool
from app.agents.tools.card_tool import CardTool
from app.agents.tools.transaction_tool import TransactionTool
from app.agents.tools.kyc_tool import KycTool
from app.agents.tools.ticket_tool import TicketTool
from app.agents.tools.user_tool import UserTool
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

REQUIRED_IDS: dict[str, tuple[str, str]] = {
    "get_balance": (
        "account_id",
        "Please share your account ID (e.g. ACC-1001).",
    ),
    "get_account_details": (
        "account_id",
        "Please share your account ID (e.g. ACC-1001).",
    ),
    "recent_transactions": (
        "account_id",
        "Please share your account ID (e.g. ACC-1001).",
    ),
    "spending_summary": (
        "account_id",
        "Please share your account ID (e.g. ACC-1001).",
    ),
    "check_case_status": (
        "case_id",
        "Please share your case ID (e.g. CASE-3001).",
    ),
    "get_case": (
        "case_id",
        "Please share your case ID (e.g. CASE-3001).",
    ),
    "check_ticket_status": (
        "case_id",
        "Please share your case ID (e.g. CASE-3001).",
    ),
    "get_ticket": (
        "case_id",
        "Please share your case ID (e.g. CASE-3001).",
    ),
    "get_user": (
        "user_id",
        "Please share your customer ID (e.g. user_7).",
    ),
    "kyc_status": (
        "user_id",
        "Please share your customer ID (e.g. user_7).",
    ),
    "missing_kyc_documents": (
        "user_id",
        "Please share your customer ID (e.g. user_7).",
    ),
    "kyc_verification_status": (
        "user_id",
        "Please share your customer ID (e.g. user_7).",
    ),
    "transaction_lookup": (
        "txn_id",
        "Please share transaction ID (e.g. TXN-9001) or UTR reference.",
    ),
    "transaction_status": (
        "txn_id",
        "Please share transaction ID (e.g. TXN-9001) or UTR reference.",
    ),
    "failed_transaction": (
        "txn_id",
        "Please share the failed transaction ID or UTR.",
    ),
    "pending_transaction": (
        "txn_id",
        "Please share the pending transaction ID or UTR.",
    ),
    "duplicate_transaction": (
        "txn_id",
        "Please share the transaction ID or UTR to check duplicates.",
    ),
    "create_dispute_case": (
        "user_id",
        "Please share your customer ID to create a dispute case.",
    ),
}


def normalize_id(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def card_ref(state: Agentstate):
    card_id = None
    card_last4 = normalize_id(state.get("card_last4"))
    order_ref = normalize_id(state.get("account_id"))
    if order_ref and order_ref.upper().startswith("CRD-"):
        card_id = order_ref
    return card_id, card_last4


class ToolNode:

    def resolve_user_id(self, state: Agentstate) -> str | None:
        uid = normalize_id(state.get("user_id"))
        if uid:
            return uid.lower()
        acc = normalize_id(state.get("account_id"))
        if acc and acc.upper().startswith("ACC-"):
            details = self.account_tool.get_account_details(acc)
            if details.get("success"):
                linked = details.get("account", {}).get("user_id")
                if linked:
                    return str(linked).strip().lower()
        return None

    def __init__(self, account_tool: AccountTool, card_tool: CardTool, transaction_tool: TransactionTool, kyc_tool: KycTool, ticket_tool: TicketTool, user_tool: UserTool, retriever=None):
        self.account_tool = account_tool
        self.card_tool = card_tool
        self.transaction_tool = transaction_tool
        self.kyc_tool = kyc_tool
        self.ticket_tool = ticket_tool
        self.user_tool = user_tool
        self.retriever = retriever

    def resolve_card_ref(self, state: Agentstate):
        card_id, card_last4 = card_ref(state)
        if card_id or card_last4:
            return card_id, card_last4, None

        acc = normalize_id(state.get("account_id"))
        if acc and acc.upper().startswith("ACC-"):
            linked = self.card_tool.cards_for_account(acc)
            if len(linked) == 1:
                return linked[0]["card_id"], linked[0]["last4"], None
            if len(linked) > 1:
                active = [c for c in linked if c.get("status") == "active"]
                if len(active) == 1:
                    return active[0]["card_id"], active[0]["last4"], None
                last4s = ", ".join(c["last4"] for c in linked)
                return None, None, {
                    "success": False,
                    "needs_clarification": True,
                    "message": (
                        f"Account {acc} has multiple cards (ending {last4s}). "
                        "Please tell me which card last 4 digits to use."
                    ),
                    "linked_cards": linked,
                }
        return None, None, None
        
        
    def tool_node(self, state: Agentstate):
        try:
            tool_name = state["tool_name"]
            if tool_name == "check_ticket_status":
                tool_name = "check_case_status"
            elif tool_name == "get_ticket":
                tool_name = "get_case"
            logger.info(f"ToolNode executing: {tool_name}")

            card_id, card_last4, card_clarify = None, None, None
            if tool_name in (
                "card_status",
                "block_card",
                "report_lost_stolen",
                "card_replacement",
            ):
                card_id, card_last4, card_clarify = self.resolve_card_ref(state)
                if card_clarify:
                    logger.info(f"ToolNode {tool_name}: multiple cards on account")
                    return {"tool_result": card_clarify, "action": "clarify"}
                if not card_id and not card_last4:
                    logger.info(f"ToolNode skipped {tool_name}: missing card reference")
                    return {
                        "tool_result": {
                            "success": False,
                            "needs_clarification": True,
                            "message": "Please share your card last 4 digits (e.g. 4521), card ID (CRD-7007), or the account ID we discussed earlier.",
                        },
                        "action": "clarify",
                    }

            if tool_name in REQUIRED_IDS:
                field, clarify_message = REQUIRED_IDS[tool_name]
                if field == "user_id" and tool_name in (
                    "kyc_status",
                    "missing_kyc_documents",
                    "kyc_verification_status",
                    "get_user",
                    "create_dispute_case",
                ):
                    if self.resolve_user_id(state) is None:
                        logger.info(f"ToolNode skipped {tool_name}: missing user_id")
                        return {
                            "tool_result": {
                                "success": False,
                                "needs_clarification": True,
                                "message": clarify_message,
                            },
                            "action": "clarify",
                        }
                elif normalize_id(state.get(field)) is None:
                    logger.info(f"ToolNode skipped {tool_name}: missing {field}")
                    return {
                        "tool_result": {
                            "success": False,
                            "needs_clarification": True,
                            "message": clarify_message,
                        },
                        "action": "clarify",
                    }

            if tool_name == "get_balance":
                result = self.account_tool.get_balance(state["account_id"])
                if result.get("success"):
                    linked = self.card_tool.cards_for_account(state["account_id"])
                    if linked:
                        result["linked_cards"] = linked

            elif tool_name == "get_account_details":
                result = self.account_tool.get_account_details(state["account_id"])
                if result.get("success"):
                    linked = self.card_tool.cards_for_account(state["account_id"])
                    if linked:
                        result["linked_cards"] = linked

            elif tool_name == "recent_transactions":
                result = self.account_tool.recent_transactions(state["account_id"])

            elif tool_name == "spending_summary":
                result = self.account_tool.spending_summary(state["account_id"])

            elif tool_name == "card_status":
                if card_id is None and card_last4 is None:
                    card_id, card_last4, clarify = self.resolve_card_ref(state)
                    if clarify:
                        return {"tool_result": clarify, "action": "clarify"}
                result = self.card_tool.card_status(card_id=card_id, card_last4=card_last4)

            elif tool_name == "block_card":
                if card_id is None and card_last4 is None:
                    card_id, card_last4, clarify = self.resolve_card_ref(state)
                    if clarify:
                        return {"tool_result": clarify, "action": "clarify"}
                result = self.card_tool.block_card(card_id=card_id, card_last4=card_last4)

            elif tool_name == "report_lost_stolen":
                if card_id is None and card_last4 is None:
                    card_id, card_last4, clarify = self.resolve_card_ref(state)
                    if clarify:
                        return {"tool_result": clarify, "action": "clarify"}
                result = self.card_tool.report_lost_stolen(card_id=card_id, card_last4=card_last4)

            elif tool_name == "card_replacement":
                if card_id is None and card_last4 is None:
                    card_id, card_last4, clarify = self.resolve_card_ref(state)
                    if clarify:
                        return {"tool_result": clarify, "action": "clarify"}
                result = self.card_tool.card_replacement(card_id=card_id, card_last4=card_last4)

            elif tool_name == "transaction_lookup":
                txn_id = state.get("txn_id")
                result = self.transaction_tool.transaction_lookup(
                    txn_id=txn_id if txn_id and txn_id.upper().startswith("TXN-") else None,
                    utr=txn_id if txn_id and not str(txn_id).upper().startswith("TXN-") else None,
                )

            elif tool_name == "transaction_status":
                txn_id = state.get("txn_id")
                result = self.transaction_tool.transaction_status(
                    txn_id=txn_id if txn_id and txn_id.upper().startswith("TXN-") else None,
                    utr=txn_id if txn_id and not str(txn_id).upper().startswith("TXN-") else None,
                )

            elif tool_name == "failed_transaction":
                txn_id = state.get("txn_id")
                result = self.transaction_tool.failed_transaction(
                    txn_id=txn_id if txn_id and txn_id.upper().startswith("TXN-") else None,
                    utr=txn_id if txn_id and not str(txn_id).upper().startswith("TXN-") else None,
                )

            elif tool_name == "pending_transaction":
                txn_id = state.get("txn_id")
                result = self.transaction_tool.pending_transaction(
                    txn_id=txn_id if txn_id and txn_id.upper().startswith("TXN-") else None,
                    utr=txn_id if txn_id and not str(txn_id).upper().startswith("TXN-") else None,
                )

            elif tool_name == "duplicate_transaction":
                txn_id = state.get("txn_id")
                result = self.transaction_tool.duplicate_transaction(
                    txn_id=txn_id if txn_id and txn_id.upper().startswith("TXN-") else None,
                    utr=txn_id if txn_id and not str(txn_id).upper().startswith("TXN-") else None,
                )

            elif tool_name == "kyc_status":
                result = self.kyc_tool.kyc_status(self.resolve_user_id(state))

            elif tool_name == "missing_kyc_documents":
                result = self.kyc_tool.missing_kyc_documents(self.resolve_user_id(state))

            elif tool_name == "kyc_verification_status":
                result = self.kyc_tool.kyc_verification_status(self.resolve_user_id(state))

            elif tool_name == "check_case_status":
                result = self.ticket_tool.check_ticket_status(
                    state["case_id"]
                )

            elif tool_name == "get_case":
                result = self.ticket_tool.get_tickets(
                    state["case_id"]
                )

            elif tool_name == "create_dispute_case":
                result = self.ticket_tool.create_dispute_case(
                    self.resolve_user_id(state),
                    account_id=state.get("account_id"),
                    txn_id=state.get("txn_id"),
                )

            elif tool_name == "get_user":
                result = self.user_tool.get_user(self.resolve_user_id(state))

            else:
                result = {
                    "success": False,
                    "message": f"Unknown tool: {tool_name}"
                }
                logger.warning(f"ToolNode encountered unknown tool: {tool_name}")

            logger.info(f"ToolNode result success: {result.get('success', False)}")
            docs = []
            if self.retriever and state.get("ticket"):
                try:
                    docs = self.retriever.similarity_search(state["ticket"])
                except Exception as ex:
                    logger.warning(f"ToolNode retriever fallback failed: {ex}")

            return {
                "tool_result": result,
                "documents": docs,
            }
            
        except Exception as e:
            logger.error(f"Error in ToolNode executing {state.get('tool_name')}: {str(e)}")
            raise CustomException(f"ToolNode Failed", e)
