from app.agents.state import Agentstate
from app.agents.tools.order_tool import OrderTool
from app.agents.tools.ticket_tool import TicketTool
from app.agents.tools.user_tool import UserTool
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

# tool_name -> (state key, prompt when the ID is missing)
_REQUIRED_IDS: dict[str, tuple[str, str]] = {
    "track_order": (
        "order_id",
        "Please share your order ID (e.g. ORD-1011) or tracking ID (e.g. TRK-1001) so I can look it up.",
    ),
    "cancel_order": (
        "order_id",
        "Please share the order ID you want to cancel (e.g. ORD-1011).",
    ),
    "check_return_eligibility": (
        "order_id",
        "Please share your order ID (e.g. ORD-1011) so I can check return eligibility.",
    ),
    "check_ticket_status": (
        "ticket_id",
        "Please share your support ticket ID (e.g. T-3001).",
    ),
    "get_ticket": (
        "ticket_id",
        "Please share your support ticket ID (e.g. T-3001).",
    ),
    "get_user": (
        "user_id",
        "Please share your user ID (e.g. user_7) or the email on your account.",
    ),
}


def _normalize_id(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


class ToolNode:
    
    
    def __init__(self , order_tool:OrderTool , ticket_tool:TicketTool , user_tool: UserTool):
        self.order_tool = order_tool
        self.ticket_tool = ticket_tool
        self.user_tool = user_tool
        
        
    def tool_node(self, state: Agentstate):
        try:
            tool_name = state["tool_name"]
            logger.info(f"ToolNode executing: {tool_name}")

            if tool_name in _REQUIRED_IDS:
                field, clarify_message = _REQUIRED_IDS[tool_name]
                if _normalize_id(state.get(field)) is None:
                    logger.info(f"ToolNode skipped {tool_name}: missing {field}")
                    return {
                        "tool_result": {
                            "success": False,
                            "needs_clarification": True,
                            "message": clarify_message,
                        },
                        "action": "clarify",
                    }

            if tool_name == "track_order":
                result = self.order_tool.track_order(state["order_id"])

            elif tool_name == "cancel_order":
                result = self.order_tool.cancel_order(state["order_id"])

            elif tool_name == "check_return_eligibility":
                result = self.order_tool.check_return_eligibility(
                    state["order_id"]
                )

            elif tool_name == "check_ticket_status":
                result = self.ticket_tool.check_ticket_status(
                    state["ticket_id"]
                )

            elif tool_name == "get_ticket":
                result = self.ticket_tool.get_tickets(
                    state["ticket_id"]
                )

            elif tool_name == "get_user":
                result = self.user_tool.get_user(
                    state["user_id"]
                )

            else:
                result = {
                    "success": False,
                    "message": f"Unknown tool: {tool_name}"
                }
                logger.warning(f"ToolNode encountered unknown tool: {tool_name}")

            logger.info(f"ToolNode result success: {result.get('success', False)}")
            return {
                "tool_result": result
            }
            
        except Exception as e:
            logger.error(f"Error in ToolNode executing {state.get('tool_name')}: {str(e)}")
            raise CustomException(f"ToolNode Failed", e)