from app.schema.classify import ClassificationSchema
from app.prompts.classify_prompt import CLASSIFY_PROMPT
from app.agents.state import Agentstate
from app.agents.session_context import format_session_context
from app.rag.llm import LLM
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

class Classifynode:
    
    def __init__(self, llm):
        self.llm = llm
    
    def classify_node(self, state:Agentstate):
        try:
            logger.info("ClassifyNode started")
            structured_llm = self.llm.with_structured_output(
                ClassificationSchema, method="json_schema"
            )
            
            chain = CLASSIFY_PROMPT | structured_llm
            
            result = chain.invoke({
                "ticket": state["ticket"],
                "session_context": format_session_context(state),
                "history": state.get("messages", [])[-4:],
            })
            
            logger.info(f"ClassifyNode result: category={result.category}, action={result.action}")
            
            return {
                    "category": result.category,
                    "urgency": result.urgency,
                    "sentiment": result.sentiment,
                    "action": result.action,
                    "tool_name": result.tool_name
            }
        except Exception as e:
            logger.error(f"Error in ClassifyNode: {str(e)}")
            raise CustomException(f"ClassifyNode Failed", e)
