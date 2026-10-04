from app.agents.state import Agentstate
from langchain_core.messages import AIMessage
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

class Generatenode:
    
    def __init__(self, generator):
        self.generator = generator
        
    def generate_node(self, state: Agentstate):
        try:
            logger.info("GenerateNode started")

            if state.get("action") == "blocked":
                logger.info("GenerateNode: Request was blocked")
                return {
                    "response": state.get("response", "I'm unable to process that request."),
                    "messages": [AIMessage(content=state.get("response", ""))],
                }

            docs = state.get("documents", [])
            tool_result = state.get("tool_result")
            action = state.get("action")
            history = state.get("messages", [])[-12:]

            response = self.generator.generate(
                ticket=state["ticket"],
                action=action,
                documents=docs,
                tool_result=tool_result,
                history=history,
                account_id=state.get("account_id"),
                case_id=state.get("case_id"),
                card_last4=state.get("card_last4"),
                txn_id=state.get("txn_id"),
            )

            logger.info("GenerateNode generated response successfully")
            return {
                "response": response.content,
                "messages": [AIMessage(content=response.content)],
            }
            
        except Exception as e:
            logger.error(f"Error in GenerateNode: {str(e)}")
            raise CustomException(f"GenerateNode Failed", e)
