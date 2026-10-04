# Technical Components, Security & Architecture Decisions — NexaBank AI

This document provides in-depth technical analysis of the security architecture, error propagation, testing strategies, deployment setups, and architectural trade-off decisions in NexaBank AI.

---

## 1. Security Architecture

### Current Security Implementation
1. **Zero-LLM Guardrail Filter (`app/agents/nodes/guard_node.py`)**:
   - Rejects prompt-injection strings (`ignore previous instructions`, `dan mode`, `jailbreak`, `override system`) using compiled regular expressions before calling any LLM.
   - Rejects non-banking off-topic messages with a helpful refusal message.
2. **PII & Data Masking (`app/prompts/generate_prompt.py`)**:
   - Explicit prompt-level guardrails: System prompt strictly forbids repeating full card numbers, CVVs, PINs, or OTPs.
   - Enforces masking (e.g. `****4521`).
3. **Sliding-Window Rate Limiting (`app/middleware/rate_limiter.py`)**:
   - Redis-backed rate limiter enforcing a maximum of 5 requests per 60-second window per `X-Thread-ID` header (or client IP address). Returns HTTP 429 when exceeded.
4. **Grounded Synthesis Constraints**:
   - When answering policy questions (`action: "retrieve"`), the generator is explicitly instructed to cite facts only from retrieved context and refuse hallucination.
   - When answering transactional questions (`action: "call_tool"`), the generator uses `tool_result` as the single source of truth.
5. **CORS Security (`app/api.py`)**:
   - Configured with `CORSMiddleware` to allow communication from authorized client interfaces.

### Production Hardening Roadmap
- **mTLS Authentication**: Mutual TLS authentication between the FastAPI gateway and internal Core Banking Systems.
- **JWT / OAuth2 Authorization**: Validating customer session tokens (`Authorization: Bearer <jwt>`) against a bank IAM provider (e.g. Keycloak, Auth0) before executing account mutations.
- **Field-Level Encryption**: Encrypting sensitive database fields (balances, phone numbers) at rest using AES-256 GCM.
- **Llama-Guard / NeMo Guardrails**: Secondary neural guardrail classifier for toxic/jailbreak inputs running locally on GPU.

---

## 2. Error Handling & Recovery Architecture

```
Error Source
  │
  ├──► Invalid/Missing Parameters (e.g. missing card_last4 in tool call)
  │      └── Handled by: ToolNode (returns {"needs_clarification": True, "action": "clarify"})
  │            └── Generator asks customer politely for the missing ID.
  │
  ├──► Prompt Injection / Off-Topic Query
  │      └── Handled by: GuardNode (returns {"action": "blocked", "response": "..."})
  │            └── Generator outputs refusal without calling any LLM.
  │
  ├──► Vector DB / Qdrant Unreachable on Startup
  │      └── Handled by: app/api.py (raises RuntimeError with actionable .env check instructions).
  │
  ├──► Node Execution Runtime Exception
  │      └── Handled by: CustomException wrapper + logger.error logging
  │            └── app/api.py catches exception and returns HTTP 500 stream with traceback details.
  │
  └──► Rate Limit Exceeded (> 5 req / 60s)
         └── Handled by: RateLimitMiddleware (returns HTTP 429 JSON response with retry_after_seconds).
```

---

## 3. Testing Architecture

The repository contains two independent testing suites:

### 3.1 Static & Integration Tests (`tests/test_banking_static.py`)
- **Framework**: `pytest`.
- **Purpose**: Fast, deterministic functional regression testing without making live LLM API calls.
- **Coverage**:
  - `test_mock_db_sizes()`: Verifies that all 6 JSON mock databases contain at least 25 seed records each.
  - `test_rag_loader_and_chunking()`: Verifies that `Loader` and `Chunker` properly split documents and parse markdown metadata.
  - `test_tool_node_banking_paths()`: Tests tool dispatching for `get_balance`, `card_status`, and missing ID clarification.
  - `test_card_linked_to_account_session()`: Verifies that passing only an `account_id` properly resolves the linked card in `ToolNode`.
  - `test_guard_and_router()`: Validates that injection strings are blocked and legitimate IDs/keywords pass.
  - `test_kyc_user_resolution_from_account()`: Verifies that customer `user_id` is automatically discovered from account data.
  - `test_streamlit_and_api_syntax()`: AST parsing verifying code syntax integrity.
- **How to Run**:
  ```bash
  pytest tests/test_banking_static.py -v
  ```

### 3.2 Automated Quality Evaluation (`tests/evaluate_quality.py`)
- **Framework**: `DeepEval`.
- **Purpose**: Evaluates 50 production scenarios (`tests/eval_dataset.json`) using an LLM Judge (`OPENAI_EVAL_MODEL`).
- **Metrics**:
  - **Answer Relevancy** (threshold: `0.7`): Measures if the response directly addresses the user's intent.
  - **Hallucination Metric** (threshold: `0.5`): Measures if factual statements in the output are contradicted by context.
  - **Contextual Precision** (threshold: `0.7`): Evaluates retrieval ranking quality for `action: "retrieve"` cases.
  - **Node-Level Accuracy**: Evaluates accuracy of Category, Action, Tool, and Account ID extraction against golden labels.
- **How to Run**:
  ```bash
  python tests/evaluate_quality.py
  ```

---

## 4. Deployment Architecture

```
[Local Development]
├── FastAPI API (:8000)
├── Redis Stack (:6379 & :8001)
└── Next.js Client (:3001) / Streamlit (:8501)
       │
       ▼
[Container Build (Dockerfile)]
├── Python 3.12-slim base
├── PyTorch CPU pre-installation
├── pip install -r requirements.txt
└── Copy application & data assets
       │
       ▼
[Multi-Container Compose (docker-compose.yml)]
├── redis: redis/redis-stack:latest (ports 6379, 8001)
├── api: FastAPI with Uvicorn (port 8000, depends on redis)
│        Healthcheck: curl http://127.0.0.1:8000/health (interval 10s)
└── ui: Streamlit Client (port 8501, depends on api health)
```

---

## 5. Architectural Decisions & Trade-Offs

### 1. Why LangGraph over AutoGen / CrewAI / Raw LangChain Chains?
- **Problem**: Banking workflows require deterministic state transitions. If a customer provides an account ID, we must validate it before calling a tool; if a request is malicious, it must never reach the LLM.
- **Why LangGraph**: LangGraph models the conversation as a formal State Graph with cyclic capabilities and native state checkpointing (`RedisSaver`).
- **Trade-off**: Requires explicit state typing (`Agentstate`) and edge management compared to autonomous multi-agent frameworks, but eliminates unpredictable agent loops.

### 2. Why Hybrid RAG (Dense Qdrant + Sparse BM25)?
- **Problem**: Dense semantic search alone struggles with exact alphanumeric banking terms (e.g. `T+5`, `NEFT batch`, `Section 25`, `₹100/day`). Sparse BM25 alone fails when customers use conversational synonyms.
- **Why Hybrid**: `EnsembleRetriever` combines dense 768-D vectors (BGE-base-en) and sparse BM25 at a 0.5/0.5 ratio, ensuring both conceptual understanding and exact term precision.
- **Trade-off**: Requires maintaining both an external Qdrant index and an in-memory BM25 index on startup.

### 3. Why RedisSaver for State Persistence?
- **Problem**: Multi-turn support conversations require remembering account numbers, card suffixes, and previous context across separate HTTP requests.
- **Why RedisSaver**: Integrates directly with LangGraph's checkpointer protocol. Keyed by `thread_id`, state is serialized and persisted with sub-millisecond retrieval latency.
- **Trade-off**: Adds a Redis dependency to the infrastructure stack.

### 4. Why a Zero-LLM Guard Node?
- **Problem**: Passing adversarial or off-topic prompts to an LLM wastes API tokens and increases round-trip latency by 500-1000ms.
- **Why Regex Guard**: Pre-screening with regular expressions blocks common injection vectors and off-topic queries in **< 1ms** with zero API cost.
- **Trade-off**: Static regex lists cannot catch novel, highly subtle adversarial linguistic tricks, which is why the generator node also contains safety guardrails.

### 5. Why Structured Output (`with_structured_output`) for Classification & Entity Extraction?
- **Problem**: Free-form text prompts produce inconsistent JSON formatting, leading to parsing errors in downstream routing logic.
- **Why Pydantic Schemas**: Enforces rigid schemas (`ClassificationSchema`, `EntitySchema`) using OpenAI's constrained JSON schema decoding, guaranteeing valid types for `category`, `action`, and `tool_name`.
- **Trade-off**: Constrained decoding introduces a slight generation latency overhead (~100ms) compared to raw unconstrained text generation.
