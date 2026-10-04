# System Architecture — Intelligent Banking Assistant

This document describes how components connect, how a chat request flows end-to-end, and how LangGraph state is checkpointed in Redis. All diagrams use **Mermaid**.

← [Back to README](README.md)

---

## 1. System context

```mermaid
flowchart TB
    subgraph Users
        U[Customer / Tester]
    end

    subgraph Presentation
        UI[Streamlit UI<br/>app/main.py]
    end

    subgraph Application
        API[FastAPI<br/>app/api.py]
        LG[LangGraph agent<br/>app/agents/graph.py]
    end

    subgraph DataAndAI
        OAI[(OpenAI API)]
        QD[(Qdrant Cloud<br/>banking_support)]
        HF[HuggingFace embeddings<br/>bge-base-en-v1.5]
        MOCK[(Mock JSON DB<br/>support-agent-data/mock_db)]
        KB[(Knowledge base<br/>policies + resolved cases)]
    end

    subgraph Infrastructure
        RD[(Redis Stack<br/>checkpoint + rate limit)]
    end

    U --> UI
    UI -->|POST /chat stream<br/>X-Thread-ID| API
    API -->|import-time load| LG
    API -.->|index if empty| QD
    API -.->|read| KB
    API -.->|embed| HF

    LG --> OAI
    LG --> QD
    LG --> MOCK
    LG --> RD
    API --> RD
```

---

## 2. Deployment (Docker Compose)

```mermaid
flowchart LR
    subgraph Host["Docker host"]
        subgraph redis_svc["service: redis"]
            R[redis/redis-stack<br/>:6379 / :8001]
        end
        subgraph api_svc["service: api"]
            A[uvicorn app.api:app<br/>:8000]
        end
        subgraph ui_svc["service: ui"]
            S[streamlit app/main.py<br/>:8501]
        end
    end

    Browser((Browser)) --> S
    S -->|API_URL=http://api:8000/chat| A
    A -->|REDIS_URL=redis://redis:6379| R
    A -->|healthcheck| A
    S -->|depends_on api healthy| A
```

| Container | Role |
|-----------|------|
| `support_redis` | LangGraph `RedisSaver`, rate-limit counters, RedisInsight on 8001 |
| `support_api` | Loads RAG + graph in a background thread; exposes `/health` and `/chat` |
| `support_ui` | Chat UI; one UUID `thread_id` per conversation |

---

## 3. API startup sequence

All RAG and graph setup runs **when `app.api` is imported** (before Uvicorn listens). Until that finishes, nothing is bound on port 8000.

```mermaid
sequenceDiagram
    participant Uvicorn
    participant API as app/api.py
    participant Q as Qdrant
    participant G as AgentGraph

    Uvicorn->>API: import app (loads KB, embeddings, Qdrant, graph)
    API->>Q: exists / upload chunks
    API->>G: AgentGraph + RedisSaver.setup()
    Uvicorn->>Uvicorn: bind :8000
    Note over API: GET /health → 200 ok
```

---

## 4. Chat request sequence (single turn)

The graph runs once per message (classify + entity + **one** generate LLM call). The HTTP layer **chunks** `result["response"]` for the UI stream—no second LLM call.

```mermaid
sequenceDiagram
    participant UI as Streamlit
    participant API as FastAPI /chat
    participant RL as Rate limiter
    participant LG as LangGraph
    participant RD as Redis checkpoint
    participant LLM as OpenAI
    participant RAG as Hybrid retriever
    participant TOOL as ToolNode

    UI->>API: POST ticket + thread_id
    API->>RL: incr key (thread or IP)
    alt over limit
        API-->>UI: 429
    end
    API->>LG: graph.invoke(state, thread_id)
    LG->>RD: load / merge checkpoint
    LG->>LG: guard → classify → entity
    alt action retrieve
        LG->>RAG: similarity_search
        RAG-->>LG: policy chunks
    else action call_tool
        LG->>TOOL: mock JSON lookup
        TOOL-->>LG: tool_result
    end
    LG->>LLM: generate_node (final answer)
    LG->>RD: save checkpoint
    LG-->>API: final state (response text)
    API-->>UI: text/plain chunks (replay response, no extra LLM)
```

---

## 5. LangGraph agent flow

```mermaid
flowchart TD
    START((START)) --> guard[Guard Node<br/>rules + keywords + IDs]
    guard -->|action blocked| generator[Generator Node]
    guard -->|pass| classify[Classify Node<br/>structured LLM]
    classify --> entity[Entity Extractor<br/>structured LLM]
    entity --> router{action?}

    router -->|retrieve| retriever[Retriever Node<br/>Qdrant + BM25]
    router -->|call_tool| tool[Tool Node<br/>mock banking APIs]
    router -->|clarify / escalate / respond| generator

    retriever --> generator
    tool --> generator
    generator --> END((END))
```

**Guard** (no LLM): blocks prompt-injection patterns and off-topic messages; allows banking keywords, banking IDs (`ACC-`, `CRD-`, `TXN-`, `CASE-`), `user_<n>`, and short follow-ups.

**Router** (`app/agents/router.py`): returns `state["action"]` as the next edge name.

---

## 6. Agent state (`Agentstate`)

Checkpointed per `thread_id` in Redis (messages + banking IDs persist across turns).

```mermaid
classDiagram
    class Agentstate {
        +messages: list~BaseMessage~
        +ticket: str
        +category: str
        +urgency: str
        +sentiment: str
        +action: str
        +tool_name: str
        +documents: list~Document~
        +tool_result: dict
        +response: str
        +account_id: str?
        +case_id: str?
        +user_id: str?
        +card_last4: str?
        +txn_id: str?
    }
```

| Field | Set by | Purpose |
|-------|--------|---------|
| `messages` | Each turn (`HumanMessage` + `AIMessage`) | Classify / entity / generate history |
| `account_id`, `card_last4`, … | Entity node (+ regex fallbacks) | Tool args and session context |
| `documents` | Retriever | Policy text for RAG answers |
| `tool_result` | Tool node | Balances, card rows, KYC JSON |
| `action`, `tool_name` | Classify | Routing |

`format_session_context()` injects known IDs into classify and entity prompts for follow-ups (“my card”, “user_3” only, etc.).

---

## 7. Hybrid RAG pipeline

```mermaid
flowchart LR
    subgraph Ingest["Startup ingest (api import)"]
        MD[Policy .md files]
        RTJSON[resolved_tickets.json]
        L[Loader]
        C[Chunker 500/100]
        E[Embeddings]
        MD --> L
        RTJSON --> L
        L --> C
        C --> E
        E -->|first run only| QD[(Qdrant collection)]
    end

    subgraph Query["Per retrieve action"]
        Q[User ticket]
        D[Dense k=2]
        B[BM25 k=2]
        ENS[EnsembleRetriever 0.5/0.5]
        Q --> D
        Q --> B
        D --> ENS
        B --> ENS
        ENS --> CHUNKS[Top chunks]
    end

    QD --> D
    C -.->|in-memory docs| B
```

Collection name: **`banking_support`** (768-d vectors).

---

## 8. Tool layer (mock core banking)

```mermaid
flowchart TB
    TN[Tool Node]

    TN --> AT[AccountTool<br/>balance, details, txns]
    TN --> CT[CardTool<br/>status, block, lost, replacement]
    TN --> TT[TransactionTool<br/>lookup, status, failed/pending]
    TN --> KT[KycTool<br/>status, missing docs]
    TN --> TK[TicketTool<br/>cases, disputes]
    TN --> UT[UserTool<br/>profile]

    AT --> JSON[(accounts.json<br/>transactions.json)]
    CT --> JSON2[(cards.json)]
    KT --> JSON3[(kyc.json)]
    TK --> JSON4[(tickets.json)]
    UT --> JSON5[(users.json)]
```

**Clarify path:** if a required ID is missing, Tool node sets `action: clarify` instead of failing.

**Account → card linking:** `card_status` with only `account_id` uses `cards_for_account()` (single active card auto-selected).

**Account → user for KYC:** `resolve_user_id()` reads `user_id` from state or from `get_account_details(account_id)`.

**Writes:** `persist.save_json()` updates `cards.json` / `tickets.json` for block, replacement, new dispute case (`mutation: true` in tool result).

---

## 9. Classify actions and tools

| `action` | Next node | When |
|----------|-----------|------|
| `retrieve` | Retriever | Policies, FAQs, fees, UPI rules |
| `call_tool` | Tool | Live mock data (balance, card, txn, KYC, case) |
| `clarify` | Generator | Ask for missing ID |
| `escalate` | Generator | Fraud / legal / human handoff |
| `respond` | Generator | Greetings, generic reply |

| Tool group | Names |
|------------|--------|
| Account | `get_balance`, `get_account_details`, `recent_transactions`, `spending_summary` |
| Card | `card_status`, `block_card`, `report_lost_stolen`, `card_replacement` |
| Transaction | `transaction_lookup`, `transaction_status`, `failed_transaction`, `pending_transaction`, `duplicate_transaction` |
| KYC | `kyc_status`, `missing_kyc_documents`, `kyc_verification_status` |
| Case / user | `check_case_status`, `get_case`, `create_dispute_case`, `get_user` |

Legacy aliases: `check_ticket_status` → `check_case_status`, `get_ticket` → `get_case`.

---

## 10. Redis usage

```mermaid
flowchart TB
    subgraph RedisStack["Redis Stack"]
        CP[LangGraph RedisSaver<br/>thread_id checkpoints]
        RL[Rate limit keys<br/>ratelimit:thread:* / ratelimit:ip:*]
    end

    LG[LangGraph invoke] --> CP
    API[FastAPI middleware] --> RL
```

| Concern | Implementation |
|---------|----------------|
| Conversation memory | `RedisSaver(REDIS_URL)` + `configurable.thread_id` |
| Rate limiting | `RateLimitMiddleware` — 5 req / 60s on `/chat` |
| Why Redis Stack | RediSearch indexes required by `langgraph-checkpoint-redis` |

LangChain `ConversationBufferMemory` is **not** used; the full `Agentstate` is checkpointed instead.

---

## 11. Security and guardrails

```mermaid
flowchart LR
    IN[User message] --> G[Guard patterns]
    G -->|injection regex| BLOCK[blocked → generator refusal]
    G -->|off-topic| BLOCK
    G -->|banking / IDs / follow-up| PIPE[Classify pipeline]
    PIPE --> GEN[Generate prompt rules]
    GEN --> OUT[No full PAN/PIN/OTP<br/>tool-grounded balances]
```

- Optional **Langfuse** callbacks on `/chat` when enabled.
- Mock data only — no real core banking integration.

---

## 12. File map (runtime-critical)

| Path | Responsibility |
|------|----------------|
| `app/api.py` | Loads KB, Qdrant, graph on import; `/health`, `/chat` streaming |
| `app/agents/graph.py` | Graph compile + `run(ticket, thread_id)` |
| `app/agents/nodes/*` | Pipeline nodes |
| `app/rag/retriever.py` | Hybrid ensemble |
| `app/middleware/rate_limiter.py` | Redis rate limits |
| `app/main.py` | Streamlit UI |

---

## 13. Extension points

- Add tools in `app/agents/tools/` and wire names in `tool_node.py`, `classify_prompt.py`.
- Add policies under `support-agent-data/knowledge_base/` and re-index Qdrant (or bump collection).
- Replace `RedisSaver` with Postgres checkpoint for long-term audit (heavier ops).
- Optional: merge classify + entity into one structured LLM call (latency/cost).
- Optional: true token streaming from a single `stream()` inside `generate_node` while accumulating text for Redis checkpoint.
