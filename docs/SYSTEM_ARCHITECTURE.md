# System Architecture — NexaBank AI

This document provides a deep, comprehensive breakdown of the technical architecture, component interactions, execution nodes, and runtime flow of the **NexaBank AI** customer support system.

---

## 1. High-Level Architecture Overview

The system is built as an agentic, stateful architecture comprising a client presentation layer (Next.js / Streamlit), a FastAPI HTTP service with Redis rate-limiting middleware, a compiled LangGraph state machine, a Hybrid RAG retriever (Qdrant Cloud + BM25), a persistent Redis checkpointer, and a core-banking tool execution layer.

```mermaid
flowchart TD
    subgraph Client Layer
        Web[Next.js 16 Web App :3001]
        Streamlit[Streamlit Chat UI :8501]
    end

    subgraph API & Security Layer
        Gateway[FastAPI Gateway :8000\napp/api.py]
        RateLimiter[RateLimitMiddleware\napp/middleware/rate_limiter.py]
        RedisCache[(Redis Cache :6379\nRate Limit Keys)]
        Gateway --> RateLimiter
        RateLimiter <--> RedisCache
    end

    Web -->|HTTP POST /api/chat or :8000/chat| Gateway
    Streamlit -->|HTTP POST /chat with X-Thread-ID| Gateway

    subgraph LangGraph State Machine [app/agents/graph.py]
        START([START]) --> GuardNode[01. Guard Node\napp/agents/nodes/guard_node.py]
        
        GuardNode -->|action == 'blocked'| GenNode[06. Generator Node\napp/agents/nodes/generater_node.py]
        GuardNode -->|action == ''| ClassifyNode[02. Classify Node\napp/agents/nodes/classify_node.py]
        
        ClassifyNode --> EntityNode[03. Entity Node\napp/agents/nodes/entity_node.py]
        
        EntityNode --> RouterFunc{04. Router\napp/agents/router.py}
        
        RouterFunc -->|action == 'retrieve'| RetrieverNode[05a. Retriever Node\napp/agents/nodes/retriever_node.py]
        RouterFunc -->|action == 'call_tool'| ToolNode[05b. Tool Node\napp/agents/nodes/tool_node.py]
        RouterFunc -->|action in ['clarify', 'escalate', 'respond']| GenNode
        
        RetrieverNode --> GenNode
        ToolNode --> GenNode
        
        GenNode --> SaveCheck[(RedisSaver Checkpointer\nlanggraph-checkpoint-redis)]
        GenNode --> END([END])
    end

    RateLimiter -->|Invoke graph.run| START

    subgraph Data & Vector Retrieval
        RetrieverNode <--> HybridEngine[EnsembleRetriever\nDense 0.5 + BM25 0.5]
        HybridEngine <--> QdrantCloud[(Qdrant Cloud\n768-D BGE-base-en)]
        HybridEngine <--> BM25Index[(BM25 Sparse Index\nIn-Memory)]
    end

    subgraph Core-Banking Tools & Data Stores
        ToolNode --> AccountTool[AccountTool\napp/agents/tools/account_tool.py]
        ToolNode --> CardTool[CardTool\napp/agents/tools/card_tool.py]
        ToolNode --> TxnTool[TransactionTool\napp/agents/tools/transaction_tool.py]
        ToolNode --> KycTool[KycTool\napp/agents/tools/kyc_tool.py]
        ToolNode --> TicketTool[TicketTool\napp/agents/tools/ticket_tool.py]
        ToolNode --> UserTool[UserTool\napp/agents/tools/user_tool.py]
        
        AccountTool <--> AccountsJSON[(accounts.json)]
        CardTool <--> CardsJSON[(cards.json - Live Write)]
        TxnTool <--> TxnsJSON[(transactions.json)]
        KycTool <--> KycJSON[(kyc.json)]
        TicketTool <--> TicketsJSON[(tickets.json - Live Write)]
        UserTool <--> UsersJSON[(users.json)]
    end

    SaveCheck <--> RedisDB[(Redis DB :6379\nCheckpoints)]

    GenNode -->|Final Text Chunk Stream| Gateway
    Gateway -->|HTTP Streaming Response| Client Layer
```

---

## 2. Component Specifications

### 2.1 FastAPI Gateway & Rate Limiting Middleware
- **Name**: `FastAPI Gateway` & `RateLimitMiddleware`
- **Responsibility**: Ingests chat requests, enforces sliding-window rate limits (5 requests per 60 seconds per thread/IP), compiles the LangGraph instance on startup, and streams text chunks back to client applications.
- **Input**: `ChatRequest(ticket: str, thread_id: str)` + `X-Thread-ID` header.
- **Output**: Chunked HTTP `StreamingResponse` (MIME type `text/plain`).
- **Important Files**:
  - `app/api.py`: FastAPI server setup, lifecycle management, CORS configuration, `/health`, and `/chat` endpoint.
  - `app/middleware/rate_limiter.py`: Sliding window counter in Redis using `INCR` and `EXPIRE`.
- **Dependencies**: `fastapi`, `starlette`, `redis`, `uvicorn`.
- **Connections**: Invocated by client frontends; calls `AgentGraph.run()`.

---

### 2.2 LangGraph State Machine Orchestrator
- **Name**: `AgentGraph`
- **Responsibility**: Defines the cyclic state graph `StateGraph(Agentstate)`, compiles nodes and conditional edges, attaches `RedisSaver` checkpointer, and executes state transitions for a given conversation thread.
- **Input**: `ticket: str`, `thread_id: str`, optional `callbacks` list.
- **Output**: Dictionary representing the updated `Agentstate` containing `response`, `messages`, `category`, `urgency`, `sentiment`, `action`, `tool_name`, `documents`, `tool_result`, `account_id`, `case_id`, `user_id`, `card_last4`, and `txn_id`.
- **Important Files**:
  - `app/agents/graph.py`: Graph builder, node attachments, edge declarations, checkpointer setup, and `run()` execution harness.
  - `app/agents/state.py`: Definition of `Agentstate(TypedDict)`.
  - `app/agents/router.py`: Conditional edge routing function returning `state["action"]`.
  - `app/agents/session_context.py`: Serializer formatting known session identifiers into prompt context.
- **Dependencies**: `langgraph`, `langchain-core`, `langgraph-checkpoint-redis`.
- **Connections**: Instantiated in `app/api.py`; dispatches execution across nodes.

---

### 2.3 Guard Node (Security & Input Shield)
- **Name**: `GuardNode`
- **Responsibility**: First line of defense. Uses regex patterns to identify and reject prompt-injection attempts, jailbreaks, and off-topic conversations with **0ms LLM latency**. Passes valid banking keywords, entity IDs (`ACC-`, `CRD-`, `TXN-`, `CASE-`, `user_`), and conversational follow-ups.
- **Input**: `state: Agentstate` containing `ticket`.
- **Output**:
  - If injection or off-topic: `{"action": "blocked", "response": "<refusal message>"}`
  - If valid: `{}` (empty dict; graph proceeds to `ClassifyNode`).
- **Important Files**:
  - `app/agents/nodes/guard_node.py`
- **Dependencies**: Python standard library `re`, `app/common/logger.py`.
- **Connections**: Direct successor of `START`; transitions to `GeneratorNode` (if blocked) or `ClassifyNode` (if passed).

---

### 2.4 Classify Node (Structured Intent & Tool Router)
- **Name**: `Classifynode`
- **Responsibility**: Invokes `ChatOpenAI` (`gpt-4o-mini`, temperature 0) with Pydantic structured output (`ClassificationSchema`). Analyzes user query, conversation history (last 10 messages), and known session context to classify intent, urgency, sentiment, target action, and specific tool name.
- **Input**: `state["ticket"]`, `session_context`, `history`.
- **Output**:
  - `category`: `account` | `card` | `transaction` | `kyc` | `dispute` | `charges` | `fraud` | `general`
  - `urgency`: `low` | `medium` | `high`
  - `sentiment`: `positive` | `neutral` | `negative`
  - `action`: `retrieve` | `call_tool` | `clarify` | `escalate` | `respond`
  - `tool_name`: Name of tool (e.g. `get_balance`, `block_card`) or `none`.
- **Important Files**:
  - `app/agents/nodes/classify_node.py`
  - `app/prompts/classify_prompt.py`
  - `app/schema/classify.py`
- **Dependencies**: `langchain-openai`, `pydantic`.
- **Connections**: Follows `GuardNode`; passes output to `EntityExtractorNode`.

---

### 2.5 Entity Extractor Node
- **Name**: `EntityExtractorNode`
- **Responsibility**: Identifies and extracts banking parameters (`account_id`, `case_id`, `user_id`, `card_last4`, `txn_id`) using a structured LLM call with deterministic regex fallbacks to guarantee no identifier is missed.
- **Input**: `state["ticket"]`, `session_context`, `history`.
- **Output**: State updates dictionary containing normalized extracted IDs (e.g., `{"account_id": "ACC-1007", "card_last4": "4521"}`).
- **Important Files**:
  - `app/agents/nodes/entity_node.py`
  - `app/prompts/entity_prompt.py`
  - `app/schema/entity.py`
- **Dependencies**: `langchain-openai`, `pydantic`, `re`.
- **Connections**: Follows `ClassifyNode`; routes via `app/agents/router.py` to `RetrieverNode`, `ToolNode`, or `GeneratorNode`.

---

### 2.6 Hybrid RAG Retrieval Engine
- **Name**: `Retriever` & `RetrieverNode`
- **Responsibility**: Executes hybrid document search combining dense cosine vector similarity (Qdrant Cloud, 768-D BGE embeddings) and sparse lexical search (Rank-BM25) with equal 0.5/0.5 weighting over 9 policy markdown files and past resolved ticket records.
- **Input**: `state["ticket"]`.
- **Output**: `{"documents": list[Document]}` (top `k=2` dense + top `k=2` sparse ensembled).
- **Important Files**:
  - `app/agents/nodes/retriever_node.py`
  - `app/rag/retriever.py`
  - `app/rag/qdrant.py`
  - `app/rag/bm25.py`
  - `app/rag/embedding.py`
  - `app/rag/loader.py`
  - `app/rag/chunk.py`
- **Dependencies**: `qdrant-client`, `langchain-qdrant`, `rank-bm25`, `sentence-transformers`, `langchain-huggingface`.
- **Connections**: Invoked when `action == "retrieve"`; outputs documents to `GeneratorNode`.

---

### 2.7 Core-Banking Tool Execution Layer
- **Name**: `ToolNode`
- **Responsibility**: Validates required parameters for the selected tool, resolves user/account/card linkages (e.g., finding the card linked to an account), dispatches execution to atomic tool classes, and mutates JSON state files when necessary.
- **Input**: `state["tool_name"]`, entity keys (`account_id`, `card_last4`, `user_id`, `txn_id`, `case_id`).
- **Output**: `{"tool_result": dict}` (e.g. `{"success": True, "balance": 124580.0, "currency": "INR"}`).
- **Important Files**:
  - `app/agents/nodes/tool_node.py`: Tool dispatcher and identifier resolution.
  - `app/agents/tools/account_tool.py`: `get_balance`, `get_account_details`, `recent_transactions`, `spending_summary`.
  - `app/agents/tools/card_tool.py`: `card_status`, `block_card`, `report_lost_stolen`, `card_replacement`.
  - `app/agents/tools/transaction_tool.py`: `transaction_lookup`, `transaction_status`, `failed_transaction`, `pending_transaction`, `duplicate_transaction`.
  - `app/agents/tools/kyc_tool.py`: `kyc_status`, `missing_kyc_documents`, `kyc_verification_status`.
  - `app/agents/tools/ticket_tool.py`: `get_tickets`, `check_ticket_status`, `create_dispute_case`.
  - `app/agents/tools/user_tool.py`: `get_user`, `get_use_mail`.
  - `app/agents/tools/persist.py`: `save_json` helper.
- **Dependencies**: Python standard library `json`, `datetime`, `pathlib`.
- **Connections**: Invoked when `action == "call_tool"`; sends `tool_result` to `GeneratorNode`.

---

### 2.8 Generator Node (Grounded Response Synthesis)
- **Name**: `Generatenode`
- **Responsibility**: Synthesizes the final natural-language response strictly grounded in retrieved documents or tool results. Masks sensitive PII (never outputs full card numbers, CVVs, PINs, or OTPs).
- **Input**: `state["ticket"]`, `action`, `documents`, `tool_result`, `history`, and entity context fields.
- **Output**: `{"response": str, "messages": [AIMessage]}`.
- **Important Files**:
  - `app/agents/nodes/generater_node.py`
  - `app/rag/generate.py`
  - `app/prompts/generate_prompt.py`
- **Dependencies**: `langchain-openai`, `langchain-core`.
- **Connections**: Terminal processing node; state is saved to Redis checkpointer, and output is streamed to client.

---

### 2.9 State Persistence & Memory Checkpointer
- **Name**: `RedisSaver`
- **Responsibility**: Checkpoints entire `Agentstate` graph memory into Redis keyed by `thread_id`. Ensures multi-turn conversation persistence across turn boundaries.
- **Input**: Thread configuration `{"configurable": {"thread_id": "<uuid>"}}` + graph state.
- **Output**: Persisted turn state in Redis.
- **Important Files**:
  - `app/agents/graph.py` (instantiated via `RedisSaver(REDIS_URL)` and `memory.setup()`).
- **Dependencies**: `redis`, `langgraph-checkpoint-redis`.
- **Connections**: Redis container on port 6379; inspectable via RedisInsight on port 8001.

---

## 3. Complete End-to-End User Journey Trace

### Scenario: Customer asks *"What is my balance for account ACC-1007?"* followed by *"Block my card"*

```
[1. User Action]
Customer enters: "What is my balance for account ACC-1007?" in web UI (thread_id: "session_abc123").

[2. Frontend Client (Next.js / Streamlit)]
POST request sent to http://127.0.0.1:8000/chat
Headers: Content-Type: application/json, X-Thread-ID: session_abc123
Body: {"ticket": "What is my balance for account ACC-1007?", "thread_id": "session_abc123"}

[3. RateLimiter Middleware (app/middleware/rate_limiter.py)]
- Checks Redis key "ratelimit:thread:session_abc123"
- Counter incremented (1 <= 5) -> Request allowed.

[4. FastAPI Endpoint (app/api.py -> chat_endpoint)]
- Calls graph.run(ticket=..., thread_id="session_abc123")
- Graph loads existing state for thread_id from Redis (initially empty).

[5. GuardNode (app/agents/nodes/guard_node.py)]
- Checks regex patterns for prompt injection -> None found.
- Detects keyword "balance" and pattern "ACC-1007" -> PASS.
- Returns {} -> state["action"] remains "".

[6. ClassifyNode (app/agents/nodes/classify_node.py)]
- Ingests query and system prompt.
- LLM Output: category="account", action="call_tool", tool_name="get_balance", urgency="medium", sentiment="neutral".

[7. EntityExtractorNode (app/agents/nodes/entity_node.py)]
- Regex matches "ACC-1007".
- State updated: {"account_id": "ACC-1007"}.

[8. Router (app/agents/router.py)]
- Returns state["action"] ("call_tool").
- LangGraph transitions to "tool" node.

[9. ToolNode (app/agents/nodes/tool_node.py)]
- Dispatches to self.account_tool.get_balance("ACC-1007").
- AccountTool reads accounts.json -> finds balance: ₹1,24,580.00.
- Returns: {"tool_result": {"success": True, "account_id": "ACC-1007", "balance": 124580.0, "currency": "INR", "status": "active"}}.

[10. GeneratorNode (app/agents/nodes/generater_node.py)]
- Generates answer grounded on tool_result: "Your available balance for account ACC-1007 is ₹1,24,580.00 INR (Status: Active)."
- State saved to Redis checkpointer for thread_id "session_abc123".

[11. HTTP Streaming Layer]
- FastAPI streams text chunks via StreamingResponse to client.

--- NEXT TURN (Multi-turn Context Reuse) ---

[1. User Action]
Customer enters: "Block my card" (no card number or account provided in message).

[2. Pipeline Processing]
- GuardNode: "card", "block" -> PASS.
- ClassifyNode: Sees session context "account_id=ACC-1007" -> category="card", action="call_tool", tool_name="block_card".
- EntityNode: Reuses session account_id="ACC-1007".
- ToolNode: Calls resolve_card_ref() -> queries cards.json for cards linked to "ACC-1007" -> finds card CRD-7007 (last4: "4521").
- CardTool blocks card CRD-7007 in cards.json and writes to disk.
- GeneratorNode outputs: "Card ending 4521 (linked to account ACC-1007) has been successfully blocked."
```
