
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config.config import (
    OPENAI_API_KEY,
    OPENAI_MODEL_NAME,
    GROQ_API_KEY,
    GROQ_MODEL_NAME,
    GROQ_GEN_MODEL,
    GROQ_BASE_URL,
    KB_DIR,
    RESOLVED_TICKETS_FILE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    QDRANT_URL,
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    VECTOR_SIZE,
)
from langchain_openai import ChatOpenAI

from app.rag.llm import LLM
from app.rag.loader import Loader
from app.rag.chunk import Chunker
from app.rag.embedding import Embedding
from app.rag.qdrant import QdrantDB
from app.rag.retriever import Retriever
from app.rag.generate import Generator

from app.agents.graph import AgentGraph
from app.agents.tools.account_tool import AccountTool
from app.agents.tools.card_tool import CardTool
from app.agents.tools.transaction_tool import TransactionTool
from app.agents.tools.kyc_tool import KycTool
from app.agents.tools.ticket_tool import TicketTool
from app.agents.tools.user_tool import UserTool

from app.middleware.rate_limiter import RateLimitMiddleware

print("Loading LLM...")
llm = LLM(model=OPENAI_MODEL_NAME, api_key=OPENAI_API_KEY).get_llm()

print("Loading documents...")
loader = Loader(kb_path=KB_DIR, resolved_path=RESOLVED_TICKETS_FILE)
docs = loader.load_all_documents()

chunker = Chunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
chunks = chunker.create_text_chunks(docs)

print("Loading embedding model...")
embedding = Embedding(model_name=EMBEDDING_MODEL)
embedding_model = embedding.get_embedding()

qdrant = QdrantDB(
    qdrant_url=QDRANT_URL,
    collection_name=QDRANT_COLLECTION,
    vector_size=VECTOR_SIZE,
    api_key=QDRANT_API_KEY,
)

try:
    if qdrant.collection_exists_with_data():
        print(f"Qdrant collection '{QDRANT_COLLECTION}' already populated. Skipping upload.")
    else:
        print("First-time setup: uploading documents to Qdrant...")
        qdrant.create_collection()
        qdrant.upload_document(documents=chunks, embedding_model=embedding_model)
        print("Upload complete.")
except Exception as qdrant_err:
    raise RuntimeError(
        f"Cannot connect to Qdrant at {QDRANT_URL} (collection={QDRANT_COLLECTION}). "
        f"Check QDRANT_URL and QDRANT_API_KEY in .env. Detail: {qdrant_err}"
    ) from qdrant_err

retriever = Retriever(
    embedding_model=embedding_model,
    documents=chunks,
    qdrant_url=QDRANT_URL,
    collection_name=QDRANT_COLLECTION,
    api_key=QDRANT_API_KEY,
)

if GROQ_API_KEY:
    print(f"Loading Groq classifier ({GROQ_MODEL_NAME}) for routing & entity extraction...")
    fast_llm = ChatOpenAI(
        model=GROQ_MODEL_NAME,
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=0,
        max_tokens=300,
    )
    print(f"Loading Groq generator ({GROQ_GEN_MODEL}) for fast LPU streaming...")
    gen_llm = ChatOpenAI(
        model=GROQ_GEN_MODEL,
        api_key=GROQ_API_KEY,
        base_url=GROQ_BASE_URL,
        temperature=0,
    )
else:
    fast_llm = llm
    gen_llm = llm

# fast_llm → qwen/qwen3.8-27b  (Groq LPU) — classify + entity, ~200ms, Groq qwen bucket
# gen_llm  → gpt-oss-120b      (Groq LPU) — streaming generation, ~150ms TTFT, separate bucket
generator = Generator(gen_llm)
account_tool = AccountTool()
card_tool = CardTool()
transaction_tool = TransactionTool()
kyc_tool = KycTool()
ticket_tool = TicketTool()
user_tool = UserTool()

print("Compiling graph...")
graph = AgentGraph(
    retriever=retriever,
    generator=generator,
    classify=fast_llm,   # Groq — fast unified classify+entity
    llm=fast_llm,        # Groq — passed through (not used for generation)
    account_tool=account_tool,
    card_tool=card_tool,
    transaction_tool=transaction_tool,
    kyc_tool=kyc_tool,
    ticket_tool=ticket_tool,
    user_tool=user_tool,
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)


class ChatRequest(BaseModel):
    ticket: str
    thread_id: str


@app.get("/health")
async def health():
    return {"status": "ok", "service": "banking-assistant-api"}


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    from app.config.config import LANGFUSE_ENABLED

    callbacks = []
    if LANGFUSE_ENABLED:
        from langfuse.langchain import CallbackHandler
        langfuse_handler = CallbackHandler()
        callbacks.append(langfuse_handler)

    def real_token_stream():
        """True real-time streaming: yields LLM tokens as they are generated.
        Guard → Classify → Entity → Tool/Retriever run synchronously first,
        then GenerateNode streams token-by-token directly to the browser.
        """
        try:
            for token in graph.stream_run(
                ticket=request.ticket,
                thread_id=request.thread_id,
                callbacks=callbacks,
            ):
                yield token
        except Exception as e:
            import traceback
            error_msg = f"Streaming error: {str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            yield f"\n\n[Error: {str(e)}]"

    return StreamingResponse(real_token_stream(), media_type="text/plain")
