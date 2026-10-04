# Codebase Guide & Function Reference — NexaBank AI

This document provides a developer-focused map of the codebase, detailing every key file, its runtime responsibilities, dependencies, callers, and function-level connections.

---

## 1. Directory Structure & Responsibilities

```
support/
├── app/
│   ├── agents/                   # Core agent state machine, nodes, and tool definitions
│   │   ├── nodes/                # Individual LangGraph execution steps (Guard, Classify, Entity, Tool, RAG, Gen)
│   │   ├── tools/                # Mock core-banking business logic tools (Accounts, Cards, Txns, KYC, Cases, Users)
│   │   ├── graph.py              # LangGraph compilation & Redis checkpointer assembly
│   │   ├── router.py             # Conditional routing logic for action edges
│   │   ├── session_context.py    # Multi-turn context serializer
│   │   └── state.py              # AgentState TypedDict schema
│   ├── common/                   # Shared logging and exception wrappers
│   │   ├── custom_exception.py   # Central CustomException class
│   │   └── logger.py             # Standardized logging formatter
│   ├── config/
│   │   └── config.py             # Environment variables and path resolution
│   ├── middleware/
│   │   └── rate_limiter.py       # Sliding-window Redis rate limiter middleware
│   ├── prompts/                  # System and user prompt templates
│   │   ├── classify_prompt.py    # Multi-turn intent & action classification prompt
│   │   ├── entity_prompt.py      # Banking entity extraction prompt
│   │   └── generate_prompt.py    # Grounded response synthesis prompt with PII rules
│   ├── rag/                      # RAG components (Embedding, Qdrant, BM25, Retriever, Generator, LLM)
│   │   ├── bm25.py               # Sparse keyword search engine
│   │   ├── chunk.py              # Recursive text chunking
│   │   ├── embedding.py          # BGE-base-en-v1.5 model loader
│   │   ├── generate.py           # Generation chain wrapper
│   │   ├── llm.py                # ChatOpenAI factory
│   │   ├── loader.py             # Markdown and resolved ticket document loader
│   │   ├── qdrant.py             # Qdrant client & collection manager
│   │   └── retriever.py          # Hybrid EnsembleRetriever
│   ├── schema/                   # Pydantic schemas for structured LLM outputs
│   │   ├── classify.py           # ClassificationSchema definition
│   │   └── entity.py             # EntitySchema definition
│   ├── api.py                    # FastAPI application, startup indexing, and /chat streaming route
│   └── main.py                   # Streamlit conversational interface
├── support-agent-data/
│   ├── knowledge_base/           # Verified bank policy documents & resolved tickets
│   └── mock_db/                  # Core banking JSON seed databases
├── tests/
│   ├── eval_dataset.json         # 50 production test cases
│   ├── evaluate_quality.py       # DeepEval automated LLM quality evaluation
│   ├── node_eval_results.json    # Per-node accuracy output logs
│   └── test_banking_static.py    # Pytest static & functional regression suite
├── web/                          # Next.js 16 frontend application
│   ├── src/app/                  # App router pages & API proxy route
│   └── src/components/           # Live Copilot & UI sections
├── docker-compose.yml            # Multi-service container orchestration
├── Dockerfile                    # Python environment container definition
└── requirements.txt              # Core Python dependencies
```

---

## 2. File-by-File Technical Specification

### `app/api.py`
- **Purpose**: Main FastAPI application entry point. Initializes embeddings, validates or populates Qdrant collection on startup, instantiates `AgentGraph`, applies `RateLimitMiddleware`, and exposes `/health` and `/chat` routes.
- **Used By**: Uvicorn server, Docker Compose `api` service, Next.js / Streamlit frontends.
- **Depends On**: `app.config.config`, `app.rag.*`, `app.agents.graph.AgentGraph`, `app.agents.tools.*`, `app.middleware.rate_limiter.RateLimitMiddleware`.
- **Key Functions / Routes**:
  - `health()`: GET `/health` -> Returns `{"status": "ok", "service": "banking-assistant-api"}`.
  - `chat_endpoint(request: ChatRequest)`: POST `/chat` -> Executes `graph.run()` and returns a `StreamingResponse` with text chunks.

---

### `app/agents/graph.py`
- **Purpose**: Builds and compiles the LangGraph state machine. Attaches nodes (`guard`, `classify`, `entity_extractor`, `retriever`, `tool`, `generator`), defines conditional edges, connects to Redis via `RedisSaver`, and executes multi-turn queries.
- **Used By**: `app/api.py`, `tests/test_banking_static.py`, `tests/evaluate_quality.py`.
- **Depends On**: `langgraph.graph.StateGraph`, `app.agents.state.Agentstate`, `app.agents.nodes.*`, `app.agents.router.router`, `langgraph.checkpoint.redis.RedisSaver`.
- **Key Classes / Methods**:
  - `AgentGraph.__init__(...)`: Assembles nodes, adds conditional edges, initializes `RedisSaver(REDIS_URL)`, and runs `memory.setup()`.
  - `AgentGraph.run(ticket: str, thread_id: str, callbacks=None)`: Retrieves previous turn state from Redis, initializes state dictionary, and invokes `self.graph.invoke()`.

---

### `app/agents/nodes/guard_node.py`
- **Purpose**: Zero-LLM security barrier. Uses compiled regex patterns and keyword lists to immediately block prompt-injection attacks (`ignore previous instructions`, `dan mode`, `jailbreak`) and non-banking off-topic queries.
- **Used By**: `AgentGraph` (first node after `START`).
- **Depends On**: `app.agents.state.Agentstate`, `app.common.logger`, `app.common.custom_exception`.
- **Key Methods**:
  - `GuardNode.guard_node(state: Agentstate) -> dict`: Evaluates `state["ticket"]`. Returns `{"action": "blocked", "response": "..."}` if malicious/off-topic; returns `{}` if valid.

---

### `app/agents/nodes/classify_node.py`
- **Purpose**: Structured classification step. Invokes GPT-4o-mini with `ClassificationSchema` to determine intent category, urgency, sentiment, action (`retrieve`, `call_tool`, `clarify`, `escalate`, `respond`), and tool name.
- **Used By**: `AgentGraph`.
- **Depends On**: `app.schema.classify.ClassificationSchema`, `app.prompts.classify_prompt.CLASSIFY_PROMPT`, `app.agents.session_context.format_session_context`.
- **Key Methods**:
  - `Classifynode.classify_node(state: Agentstate) -> dict`: Returns dictionary with updated `category`, `urgency`, `sentiment`, `action`, and `tool_name`.

---

### `app/agents/nodes/entity_node.py`
- **Purpose**: Extracts parameters (`account_id`, `case_id`, `user_id`, `card_last4`, `txn_id`) using structured output with regex fallbacks to ensure deterministic capture.
- **Used By**: `AgentGraph`.
- **Depends On**: `app.schema.entity.EntitySchema`, `app.prompts.entity_prompt.ENTITY_PROMPT`, `app.agents.session_context.format_session_context`.
- **Key Methods**:
  - `EntityExtractorNode.entity_extractor_node(state: Agentstate) -> dict`: Returns dictionary of extracted ID updates.

---

### `app/agents/nodes/tool_node.py`
- **Purpose**: Dispatches tool calls to the appropriate tool instance. Resolves linked IDs (e.g. finding user_id from an account or card_last4 from an account) and enforces clarification prompts when required identifiers are missing.
- **Used By**: `AgentGraph` (invoked when `action == "call_tool"`).
- **Depends On**: `app.agents.tools.*`.
- **Key Methods**:
  - `ToolNode.resolve_user_id(state: Agentstate) -> str | None`: Resolves user_id directly or looks up the customer linked to `account_id` in `accounts.json`.
  - `ToolNode.resolve_card_ref(state: Agentstate) -> tuple`: Resolves card reference directly or finds the card linked to `account_id` in `cards.json`.
  - `ToolNode.tool_node(state: Agentstate) -> dict`: Executes tool function and returns `{"tool_result": result}` (or sets `action: "clarify"` if parameters are missing).

---

### `app/agents/nodes/retriever_node.py`
- **Purpose**: Executes hybrid search over Qdrant and BM25 and places retrieved documents into state.
- **Used By**: `AgentGraph` (invoked when `action == "retrieve"`).
- **Depends On**: `app.rag.retriever.Retriever`.
- **Key Methods**:
  - `RetrieverNode.retriever_node(state: Agentstate) -> dict`: Returns `{"documents": docs}`.

---

### `app/agents/nodes/generater_node.py`
- **Purpose**: Generates the final natural-language response grounded on retrieved documents or tool results, masking sensitive PII numbers.
- **Used By**: `AgentGraph` (terminal node).
- **Depends On**: `app.rag.generate.Generator`.
- **Key Methods**:
  - `Generatenode.generate_node(state: Agentstate) -> dict`: Returns `{"response": text, "messages": [AIMessage]}`.

---

### `app/rag/retriever.py`
- **Purpose**: Implements hybrid search by combining `QdrantVectorStore` (dense k=2) with `BM25Retriever` (sparse k=2) using `EnsembleRetriever` with `weights=[0.5, 0.5]`.
- **Used By**: `app/api.py` (instantiated at startup) -> passed to `RetrieverNode`.
- **Depends On**: `langchain_qdrant.QdrantVectorStore`, `langchain_community.retrievers.BM25Retriever`, `langchain_classic.retrievers.EnsembleRetriever`.
- **Key Methods**:
  - `Retriever.similarity_search(query: str) -> list[Document]`: Returns ensembled top matching documents.

---

### `app/rag/qdrant.py`
- **Purpose**: Manages Qdrant Cloud collection initialization, count checks, and document indexing.
- **Used By**: `app/api.py`.
- **Depends On**: `qdrant_client.QdrantClient`, `qdrant_client.models.VectorParams`, `qdrant_client.models.Distance`.
- **Key Methods**:
  - `QdrantDB.collection_exists_with_data() -> bool`: Returns True if collection exists and has documents.
  - `QdrantDB.create_collection()`: Creates collection with 768-D Cosine distance.
  - `QdrantDB.upload_document(documents, embedding_model)`: Embeds and uploads chunks to Qdrant.

---

### `app/middleware/rate_limiter.py`
- **Purpose**: Enforces rate limiting (5 req / 60s window) on the `/chat` route using Redis keys (`ratelimit:thread:<id>` or `ratelimit:ip:<ip>`).
- **Used By**: `app/api.py` (`app.add_middleware(RateLimitMiddleware)`).
- **Depends On**: `redis.from_url`, `starlette.middleware.base.BaseHTTPMiddleware`.
- **Key Methods**:
  - `RateLimitMiddleware.dispatch(request, call_next)`: Increments Redis counter and returns HTTP 429 if limit exceeded.

---

## 3. Function-Level Runtime Connections

```
Client sends prompt
  │
  ▼
app/api.py: chat_endpoint(request)
  │
  ▼
app/agents/graph.py: AgentGraph.run(ticket, thread_id)
  │  ├── Reads previous turn state from Redis via RedisSaver
  │  └── Calls self.graph.invoke(initial_state, config)
  │
  ▼
app/agents/nodes/guard_node.py: GuardNode.guard_node(state)
  │  ├── Regex match on INJECTION_PATTERNS
  │  └── Keyword / ID match on SUPPORT_KEYWORDS
  │
  ▼ (if passed)
app/agents/nodes/classify_node.py: Classifynode.classify_node(state)
  │  └── CLASSIFY_PROMPT | llm.with_structured_output(ClassificationSchema)
  │
  ▼
app/agents/nodes/entity_node.py: EntityExtractorNode.entity_extractor_node(state)
  │  ├── ENTITY_PROMPT | llm.with_structured_output(EntitySchema)
  │  └── Regex fallbacks (BANKING_ID_PATTERN, USER_ID_PATTERN, CARD_LAST4_PATTERN)
  │
  ▼
app/agents/router.py: router(state)
  │
  ├──► [action == 'retrieve']
  │      ▼
  │    app/agents/nodes/retriever_node.py: RetrieverNode.retriever_node(state)
  │      └── app/rag/retriever.py: EnsembleRetriever.invoke(query)
  │            ├── QdrantVectorStore.as_retriever(k=2) [Dense 768-D]
  │            └── BM25Retriever(k=2) [Sparse Keyword]
  │
  ├──► [action == 'call_tool']
  │      ▼
  │    app/agents/nodes/tool_node.py: ToolNode.tool_node(state)
  │      ├── ToolNode.resolve_user_id() / ToolNode.resolve_card_ref()
  │      └── Dispatches to:
  │            ├── AccountTool (get_balance, recent_transactions, spending_summary)
  │            ├── CardTool (card_status, block_card, report_lost_stolen, card_replacement)
  │            ├── TransactionTool (transaction_lookup, failed_transaction, pending_transaction)
  │            ├── KycTool (kyc_status, missing_kyc_documents, kyc_verification_status)
  │            ├── TicketTool (get_tickets, check_ticket_status, create_dispute_case)
  │            └── UserTool (get_user, get_use_mail)
  │
  └──► [action in 'clarify', 'escalate', 'respond', or from retriever/tool]
         ▼
       app/agents/nodes/generater_node.py: Generatenode.generate_node(state)
         ├── app/rag/generate.py: GENERATE_PROMPT | self.llm
         └── PII Masking & Grounded Synthesis
               │
               ▼
       langgraph.checkpoint.redis: RedisSaver checkpoints turn to Redis (:6379)
               │
               ▼
       app/api.py: text_chunk_stream() streams tokens via StreamingResponse
               │
               ▼
       Client renders response in UI
```

---

## 4. Project Mental Model

1. **Application Starts**: `app/api.py` loads config, embeds documents (if not in Qdrant), compiles `AgentGraph`, and starts Uvicorn on port 8000.
2. **User Enters**: User types a question in Next.js (`web/`) or Streamlit (`app/main.py`).
3. **Request Enters**: HTTP POST request arrives at `/chat` with payload `{"ticket": "...", "thread_id": "..."}`.
4. **Security Filter**: `GuardNode` verifies input without calling an LLM (blocks prompt injections immediately).
5. **Intent & Parameter Extraction**: `ClassifyNode` determines action (`call_tool` vs `retrieve`), and `EntityNode` extracts IDs (`ACC-1007`, `4521`).
6. **Data Retrieval / Tool Execution**:
   - Policy questions -> `RetrieverNode` queries Qdrant Cloud + BM25 index.
   - Account / Card operations -> `ToolNode` executes deterministic function against `mock_db/` JSON stores.
7. **Answer Synthesis**: `GeneratorNode` synthesizes verified response with masked PII numbers.
8. **Memory Persistence**: `RedisSaver` saves conversation state under `thread_id` in Redis.
9. **Streaming Delivery**: FastAPI streams tokens back to client in real-time.
10. **Testing & Validation**: Run `pytest tests/test_banking_static.py` for functional tests and `python tests/evaluate_quality.py` for DeepEval LLM evaluation.
