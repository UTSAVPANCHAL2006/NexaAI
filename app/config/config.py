import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "support-agent-data"

KB_DIR = DATA_DIR / "knowledge_base"

MOCK_DB_DIR = DATA_DIR / "mock_db"

RESOLVED_TICKETS_FILE = (
    KB_DIR
    / "past_tickets"
    / "resolved_tickets.json"
)

CHUNK_SIZE=500
CHUNK_OVERLAP = 100

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

QDRANT_URL        = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY    = os.getenv("QDRANT_API_KEY", None)
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "banking_support")
VECTOR_SIZE       = 768

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Agent + RAG generation (classify, entity, generator)
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Fast LPU inference for classification & entity extraction
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "qwen/qwen3.8-27b")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_GEN_MODEL = os.getenv("GROQ_GEN_MODEL", "openai/gpt-oss-120b")

# DeepEval offline judge (evaluate_quality.py)
OPENAI_EVAL_MODEL = os.getenv("OPENAI_EVAL_MODEL", "gpt-oss-120b")

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


ACCOUNTS_PATH = BASE_DIR / "support-agent-data" / "mock_db" / "accounts.json"
CARDS_PATH = BASE_DIR / "support-agent-data" / "mock_db" / "cards.json"
TRANSACTIONS_PATH = BASE_DIR / "support-agent-data" / "mock_db" / "transactions.json"
KYC_PATH = BASE_DIR / "support-agent-data" / "mock_db" / "kyc.json"
TICKETS_PATH = BASE_DIR / "support-agent-data" / "mock_db" / "tickets.json"
USERS_PATH = BASE_DIR / "support-agent-data" / "mock_db" / "users.json"

