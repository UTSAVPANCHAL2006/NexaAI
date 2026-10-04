# Comprehensive Interview Guide — NexaBank AI

This guide is your master playbook for explaining the **NexaBank AI** project in technical interviews, whiteboard sessions, and system design discussions.

---

## 1. Verbal Explanations by Time Limit

### ⏱️ 30-Second Elevator Pitch
> "NexaBank AI is an enterprise-grade, deterministic customer support agent built for retail banking. It uses a 6-node LangGraph state machine combining zero-LLM guardrails, hybrid vector retrieval with Qdrant and BM25, and 18 core-banking tools. It allows customers to check account balances, execute emergency card blocks, diagnose failed transactions, and get verified policy answers with multi-turn conversation memory backed by Redis."

---

### ⏱️ 1-Minute Product & Technical Overview
> "I built NexaBank AI to solve the reliability and context issues common in traditional banking chatbots. Instead of a single monolithic LLM prompt that hallucinates, NexaBank uses a deterministic LangGraph state machine. 
>
> When a user sends a query, a zero-LLM regex guard node first checks for prompt injections. If safe, a structured intent classifier and entity extractor determine the action and extract account or card IDs. 
>
> If it's a policy inquiry, a hybrid RAG retriever combines Qdrant 768-D dense vectors with BM25 sparse keyword search to pull verified banking rules. If it's an operational request—like blocking a stolen card or checking a balance—a tool node executes against banking data stores with state mutation. 
>
> Finally, a generator synthesizes a grounded answer with strict PII masking, and turn state is checkpointed in Redis so customers can ask natural follow-ups."

---

### ⏱️ 2-Minute Technical System Design Explanation
> "Let me walk you through the technical architecture of NexaBank AI. The backend is powered by FastAPI with a custom Redis sliding-window rate limiter enforcing a limit of 5 requests per 60 seconds per thread.
>
> When a message arrives at `/chat`, it enters a compiled LangGraph workflow. The first node is a Guard Node that screens inputs in under 1 millisecond using regex without spending LLM tokens. Valid queries transition to a Classify Node and Entity Extractor Node, which use GPT-4o-mini with Pydantic JSON schemas to extract parameters like account IDs and determine whether the action is `call_tool`, `retrieve`, `clarify`, `escalate`, or `respond`.
>
> For knowledge retrieval, we implemented Hybrid RAG. Dense semantic search via Qdrant Cloud handles conceptual questions, while sparse BM25 handles exact terms like 'T+5 auto-reversal' or 'NEFT batch cutoffs' at a 50/50 weighted split. 
>
> For banking actions, we have 18 tools across Account, Card, Transaction, KYC, Dispute, and User services. When a user requests a card block, the tool resolves linked cards from the account session, updates the card status in storage, and returns structured confirmation.
>
> Finally, the generator produces a verified response with PII masking, and `RedisSaver` checkpoints the state for multi-turn persistence. The entire response is streamed via chunked HTTP to our Next.js web application."

---

### ⏱️ 5-Minute Deep Technical Architecture Walkthrough
> "Let's dive into the end-to-end engineering of NexaBank AI.
>
> **1. Client & API Layer**:
> The client layer consists of a Next.js 16 web application with an interactive live copilot that connects directly to our FastAPI backend on port 8000. Before hitting business logic, every request passes through a Starlette `RateLimitMiddleware` that reads an `X-Thread-ID` header and increments a Redis sliding window key.
>
> **2. The Graph Pipeline**:
> We modeled the support agent as a directed State Graph using LangGraph. It manages an `Agentstate` TypedDict that tracks conversation history, classified intent, urgency, sentiment, action, tool results, retrieved documents, and extracted entities like `account_id`, `card_last4`, and `txn_id`.
>
> **3. Input Guarding**:
> To protect against jailbreaks and cost spikes, our Guard Node intercepts adversarial strings like 'ignore all instructions' using pre-compiled regex patterns before any LLM is called. It also verifies that the message contains banking keywords, account IDs, or conversational greetings.
>
> **4. Structured Intent & Entity Parsing**:
> If valid, the query passes to the Classify Node. We use LangChain's `with_structured_output` bound to a Pydantic `ClassificationSchema`. This returns an action enum: `retrieve`, `call_tool`, `clarify`, `escalate`, or `respond`. In parallel, the Entity Extractor Node extracts banking IDs. If an LLM fails to extract an ID like 'ACC-1007', our deterministic regex fallback captures it automatically.
>
> **5. Hybrid Retrieval vs Tool Execution**:
> A dynamic router edge inspects `state['action']`:
> - If `action == 'retrieve'`, the Retriever Node invokes an `EnsembleRetriever` combining dense vector search from Qdrant Cloud (768-D BGE embeddings) with BM25 sparse keyword search at equal 0.5 weights over our banking policies and resolved ticket dataset.
> - If `action == 'call_tool'`, the Tool Node resolves any implicit relationships—for example, if the user says 'block my card' and we have their account ID in session memory, it looks up the linked card, executes the block, writes the mutation to disk, and passes the result to the generator.
> - If required parameters are missing, the tool sets `action = 'clarify'` so the assistant asks for the missing information.
>
> **6. Grounded Generation & Checkpointing**:
> The Generator Node takes the tool result or retrieved documents, along with conversation history, and invokes GPT-4o-mini. System prompt constraints mandate zero hallucinations, strict PII masking of card numbers, and no exposure of PINs or OTPs.
>
> **7. State Persistence & Evaluation**:
> The final state is checkpointed in Redis via `RedisSaver`. For quality assurance, we have a Pytest regression suite testing deterministic logic and a DeepEval test suite running 50 production queries against Answer Relevancy, Hallucination, and Contextual Precision metrics with an LLM judge."

---

## 2. Whiteboard Architecture Diagram

```
+-------------------------------------------------------------------------------+
|                                CLIENT LAYER                                   |
|   Next.js 16 Web App (:3001)           Streamlit Chat Interface (:8501)       |
+-------------------------------------------------------------------------------+
                                      │  (HTTP POST /chat with thread_id)
                                      ▼
+-------------------------------------------------------------------------------+
|                              FASTAPI GATEWAY (:8000)                          |
|   RateLimitMiddleware (5 req / 60s window per thread_id in Redis :6379)       |
+-------------------------------------------------------------------------------+
                                      │
                                      ▼
+-------------------------------------------------------------------------------+
|                       LANGGRAPH STATE MACHINE (graph.py)                      |
|                                                                               |
|   [START] ──► [01. Guard Node] (Zero-LLM Regex injection filter)              |
|                     │                                                         |
|                     ├── (pass) ──► [02. Classify Node] (GPT-4o-mini Intent)   |
|                     │                     │                                   |
|                     │              [03. Entity Node] (Regex + LLM IDs)        |
|                     │                     │                                   |
|                     │              [04. Router Edge]                          |
|                     │               /     │     \                             |
|                     │    (retrieve)/      │      \(call_tool)                 |
|                     │             ▼       │       ▼                           |
|                     │   [05a. Retriever]  │  [05b. Tool Node]                 |
|                     │     (Qdrant+BM25)   │  (18 Banking Tools)               |
|                     │             \       │       /                           |
|                     │              \      ▼      /                            |
|                     └────────────► [06. Generator Node] (PII Masked LLM)      |
|                                           │                                   |
|                                   [RedisSaver Checkpoint] ──► [END]           |
+-------------------------------------------------------------------------------+
           │                                 │                    │
           ▼                                 ▼                    ▼
+---------------------+           +--------------------+  +--------------------+
|    QDRANT CLOUD     |           |   CORE BANKING DB  |  |    REDIS STACK     |
| 768-D BGE Embeddings|           | JSON Seed Stores   |  | Checkpoints :6379  |
| 9 Policies + Tickets|           | accounts, cards... |  | Insight UI :8001   |
+---------------------+           +--------------------+  +--------------------+
```

---

## 3. High-Frequency Interview Q&A

### Q1: Why did you choose LangGraph instead of building a single prompt or using AutoGen?
- **Short Answer**: "Banking requires strict deterministic control over tool execution, input safety, and multi-turn state. A single prompt easily hallucinates policies and fails multi-turn context, while autonomous multi-agent frameworks like AutoGen are non-deterministic and can get stuck in loops."
- **Detailed Answer**: "With LangGraph, we define our support workflow as a formal State Graph with typed state (`Agentstate`). This allows us to guarantee that the Guard Node runs first before any LLM is called, that the Entity Extractor always runs with regex validation, and that the Router directs queries to tools or RAG based on strict action enums. Furthermore, LangGraph's checkpointer protocol (`RedisSaver`) allows us to persist full session state across HTTP turn boundaries."
- **Project Example**: When a customer asks *"Why did TXN-9025 fail?"*, the graph deterministically routes `START -> Guard -> Classify -> Entity -> Router -> ToolNode (failed_transaction) -> Generator -> END`.
- **Code Location**: `app/agents/graph.py:21-45`.

---

### Q2: How does your Hybrid RAG system work, and why not use vector search alone?
- **Short Answer**: "Vector search alone struggles with exact banking terms like 'T+5 auto-reversal' or 'NEFT batch cutoffs', while keyword search fails on semantic synonyms. We combine Qdrant dense 768-D vector search with BM25 sparse keyword search using LangChain's EnsembleRetriever with 50/50 weights."
- **Detailed Answer**: "Our knowledge base consists of 9 markdown policy files and past resolved tickets chunked into 500-character chunks with 100-character overlap. In `app/rag/retriever.py`, we instantiate `QdrantVectorStore` with `BAAI/bge-base-en-v1.5` embeddings (dense k=2) and an in-memory `BM25Retriever` (sparse k=2). The `EnsembleRetriever` merges and re-ranks both result lists with reciprocal rank weighting, giving the generator exact regulatory clauses."
- **Project Example**: A query like *"What is the refund timeline for failed UPI debit?"* retrieves the exact NPCI T+5 settlement rule from `upi_policy.md`.
- **Code Location**: `app/rag/retriever.py:12-39`.

---

### Q3: How do you prevent Prompt Injections and protect sensitive banking data?
- **Short Answer**: "We implement security in layers: a Zero-LLM regex Guard Node at the graph entrypoint, prompt-level PII masking in the generator, Redis sliding-window rate limiting, and grounded synthesis constraints."
- **Detailed Answer**: 
  1. `GuardNode` tests inputs against compiled injection regexes (`ignore previous instructions`, `dan mode`, `jailbreak`) and rejects them in < 1ms with 0 API cost.
  2. The generator prompt explicitly prohibits outputting full PAN, CVV, PIN, or OTP, enforcing masked outputs (e.g. `****4521`).
  3. `RateLimitMiddleware` limits requests to 5 req / 60s per thread ID in Redis.
  4. The generator is constrained to answer exclusively using tool results or retrieved documents.
- **Code Location**: `app/agents/nodes/guard_node.py:65-134` and `app/prompts/generate_prompt.py:22-26`.

---

### Q4: How does multi-turn entity resolution work when a customer says "block it" or "my card"?
- **Short Answer**: "We store extracted entities in the graph's `Agentstate` and serialize them into system prompts via `format_session_context()`. The `ToolNode` also contains account-to-card relationship resolvers."
- **Detailed Answer**: "When a customer provides an account ID in turn 1 (e.g. `ACC-1007`), it is saved in state. On turn 2, when they say 'block my card', `format_session_context()` injects `account_id=ACC-1007` into the classifier prompt. In `ToolNode`, `resolve_card_ref()` queries `cards.json` to find the active card linked to `ACC-1007` (card `CRD-7007`, ending in `4521`) and executes the block without asking the customer to re-enter their card number."
- **Code Location**: `app/agents/session_context.py:4-18` and `app/agents/nodes/tool_node.py:128-152`.

---

### Q5: How do you evaluate the quality of the LLM responses?
- **Short Answer**: "We use DeepEval to benchmark 50 golden banking queries against Answer Relevancy, Hallucination, and Contextual Precision metrics using an LLM Judge, and log per-node accuracy metrics."
- **Detailed Answer**: "In `tests/evaluate_quality.py`, we test our dataset across three automated metrics:
  - **Answer Relevancy** (threshold 0.7): Evaluates if the answer directly addresses the prompt.
  - **Hallucination Metric** (threshold 0.5): Verifies that generated statements match tool results or retrieved docs.
  - **Contextual Precision** (threshold 0.7): Evaluates the ranking quality of retrieved RAG documents.
  We also calculate node-level accuracy for category classification, action routing, and entity extraction, saving outputs to `tests/node_eval_results.json`."
- **Code Location**: `tests/evaluate_quality.py:52-244`.

---

## 4. "Show Me The Code" Quick-Reference

| Question | File | Function / Class | Line Reference |
|---|---|---|---|
| Where does the API start? | `app/api.py` | `app = FastAPI()`, `chat_endpoint` | `api.py:102, 117` |
| Where is the graph compiled? | `app/agents/graph.py` | `AgentGraph.__init__`, `self.graph_builder.compile` | `graph.py:21-45` |
| Where is the rate limiter implemented? | `app/middleware/rate_limiter.py` | `RateLimitMiddleware.dispatch` | `rate_limiter.py:21-58` |
| Where are prompt injections blocked? | `app/agents/nodes/guard_node.py` | `GuardNode.guard_node` | `guard_node.py:102-134` |
| Where does intent classification happen? | `app/agents/nodes/classify_node.py` | `Classifynode.classify_node` | `classify_node.py:16-39` |
| Where are entity regex fallbacks? | `app/agents/nodes/entity_node.py` | `EntityExtractorNode.entity_extractor_node` | `entity_node.py:42-75` |
| Where is hybrid RAG executed? | `app/rag/retriever.py` | `Retriever.__init__`, `similarity_search` | `retriever.py:12-39` |
| Where is card blocking executed? | `app/agents/tools/card_tool.py` | `CardTool.block_card` | `card_tool.py:55-73` |
| Where is account-to-card resolved? | `app/agents/nodes/tool_node.py` | `ToolNode.resolve_card_ref` | `tool_node.py:128-152` |
| Where is PII masking enforced? | `app/prompts/generate_prompt.py` | `GENERATE_PROMPT` system template | `generate_prompt.py:22-26` |
| Where is state saved to Redis? | `app/agents/graph.py` | `RedisSaver(REDIS_URL)` checkpointer | `graph.py:42-45` |

---

## 5. Technical Challenges & Solutions

### Challenge 1: Contextual Resolution in Multi-Turn Conversations
- **Problem**: When a customer checked their balance on turn 1 (`ACC-1007`) and said *"Block my card"* on turn 2, the agent failed because the second query contained no card ID or account number.
- **Solution**: Built `format_session_context()` to serialize known session entities into the classifier prompt, and implemented `resolve_card_ref()` in `ToolNode` to inspect `cards.json` for cards linked to the active `account_id`.
- **Trade-off**: Requires an additional lookup in `cards.json`, but provides a seamless natural conversation experience.

### Challenge 2: False Hallucination Penalties in DeepEval on Tool Calls
- **Problem**: In DeepEval, evaluating `call_tool` actions against standard RAG context marked all valid tool responses as hallucinations because no vector documents were retrieved.
- **Solution**: Updated `evaluate_quality.py` to dynamically feed the serialized `tool_result` as the grounding context for tool actions and restricted `ContextualPrecisionMetric` exclusively to genuine `retrieve` actions.
- **Learning**: Evaluation metrics must be tailored to the specific execution path of the agent.

---

## 6. Project Technical Glossary

| Term | Meaning & Context in NexaBank |
|---|---|
| **LangGraph** | Cyclic state machine library used to orchestrate node execution and manage state checkpoints. |
| **Agentstate** | TypedDict holding messages, classified intent, tool results, retrieved documents, and extracted IDs. |
| **RedisSaver** | Redis-backed checkpointer storing conversation state per `thread_id`. |
| **Hybrid RAG** | Retrieval combining dense vector search (Qdrant) and sparse keyword search (BM25) with reciprocal rank weighting. |
| **Zero-LLM Guard** | Regex-based input filtering that intercepts malicious or off-topic prompts without LLM token cost or latency. |
| **DeepEval** | Unit-testing framework for LLMs evaluating semantic metrics (Relevancy, Hallucination, Precision) with an LLM judge. |
| **PII Masking** | System prompt enforcement hiding sensitive card digits (only showing last 4) and preventing PIN/OTP repetition. |
| **Sliding Window** | Redis rate-limiting algorithm enforcing 5 requests per 60 seconds per thread ID. |
