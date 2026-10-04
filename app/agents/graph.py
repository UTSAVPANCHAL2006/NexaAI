from langgraph.graph import StateGraph, START, END
from app.agents.state import Agentstate
from app.agents.nodes.retriever_node import RetrieverNode
from app.agents.nodes.generater_node import Generatenode
from app.agents.nodes.unified_node import UnifiedClassifierNode
from app.agents.nodes.tool_node import ToolNode
from app.agents.nodes.guard_node import GuardNode


from app.agents.router import router
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage



class AgentGraph:
    
    def __init__(self, retriever, generator, classify, llm, account_tool, card_tool, transaction_tool, kyc_tool, ticket_tool, user_tool):
        
        self.generator = generator  # keep reference for direct streaming
        self.graph_builder = StateGraph(Agentstate)
        
        fast_llm = classify or llm
        self.graph_builder.add_node("guard", GuardNode().guard_node)
        self.graph_builder.add_node("unified_classifier", UnifiedClassifierNode(fast_llm).unified_node)
        self.graph_builder.add_node("retriever", RetrieverNode(retriever).retriever_node)
        self.graph_builder.add_node("generator", Generatenode(generator).generate_node)
        self.graph_builder.add_node("tool", ToolNode(account_tool, card_tool, transaction_tool, kyc_tool, ticket_tool, user_tool, retriever=retriever).tool_node)

        self.graph_builder.add_edge(START, "guard")
        self.graph_builder.add_conditional_edges("guard", lambda state: state["action"], {"blocked": "generator", "": "unified_classifier"})
        self.graph_builder.add_conditional_edges("unified_classifier", router, {"retrieve": "retriever", "call_tool": "tool", "clarify": "generator", "escalate": "generator", "respond": "generator"})
        self.graph_builder.add_edge("retriever", "generator")
        self.graph_builder.add_edge("tool", "generator")
        self.graph_builder.add_edge("generator", END)

        
        # In-process memory: works on any Redis provider (no FT.* required)
        # State persists for the lifetime of the server process per thread_id.
        memory = MemorySaver()
        self.graph = self.graph_builder.compile(checkpointer=memory)
        
        
      
    def _build_initial_state(self, ticket: str, config: dict) -> dict:
        """Build initial state carrying forward entity IDs from Redis checkpoint."""
        current_state = self.graph.get_state(config).values
        return {
            "ticket": ticket,
            "messages": [HumanMessage(content=ticket)],
            "category": "",
            "urgency": "",
            "sentiment": "",
            "action": "",
            "tool_name": "",
            "documents": [],
            "tool_result": {},
            "response": "",
            # Persist entity IDs across turns
            "account_id": current_state.get("account_id") if current_state else None,
            "case_id":    current_state.get("case_id")    if current_state else None,
            "user_id":    current_state.get("user_id")    if current_state else None,
            "card_last4": current_state.get("card_last4") if current_state else None,
            "txn_id":     current_state.get("txn_id")     if current_state else None,
        }

    def run(self, ticket: str, thread_id: str = "default", callbacks=None):
        config = {"configurable": {"thread_id": thread_id}}
        if callbacks:
            config["callbacks"] = callbacks
        initial_state = self._build_initial_state(ticket, config)
        result = self.graph.invoke(initial_state, config=config)
        return result

    def stream_run(self, ticket: str, thread_id: str = "default", callbacks=None):
        """Run Guard→Classify→Entity→Tool/Retriever via graph, then stream
        GenerateNode token-by-token directly from the LLM — true real-time streaming.
        Users see the first token ~500ms earlier than fake-streaming.
        """
        config = {"configurable": {"thread_id": thread_id}}
        if callbacks:
            config["callbacks"] = callbacks

        initial_state = self._build_initial_state(ticket, config)

        # ── Step 1: Run all nodes EXCEPT generate via graph.invoke() ──────────
        # We interrupt execution before the "generator" node so we can stream it.
        # LangGraph interrupt_before stops execution right before the named node.
        interrupt_config = {**config, "interrupt_before": ["generator"]}
        partial_result = self.graph.invoke(initial_state, config=interrupt_config)

        action = partial_result.get("action", "")

        # ── Step 2: Handle blocked/injection — no LLM needed ─────────────────
        if action == "blocked":
            blocked_msg = partial_result.get("response", "I'm unable to process that request.")
            yield blocked_msg
            return

        # ── Step 3: Stream directly from Generator ────────────────────────────
        full_response = ""
        for token in self.generator.stream_generate(
            ticket=partial_result["ticket"],
            action=action,
            documents=partial_result.get("documents", []),
            tool_result=partial_result.get("tool_result"),
            history=partial_result.get("messages", [])[-4:],
            account_id=partial_result.get("account_id"),
            case_id=partial_result.get("case_id"),
            card_last4=partial_result.get("card_last4"),
            txn_id=partial_result.get("txn_id"),
        ):
            full_response += token
            yield token

        # ── Step 4: Write final state back to Redis checkpoint ────────────────
        from langchain_core.messages import AIMessage
        self.graph.update_state(
            config,
            {
                "response": full_response,
                "messages": [AIMessage(content=full_response)],
            },
        )