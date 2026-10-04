from langchain_openai import OpenAIEmbeddings

from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from app.config.config import OPENAI_API_KEY, EMBEDDING_MODEL

logger = get_logger(__name__)


class Embedding:
    """Zero-memory Cloud API Embeddings using OpenAI text-embedding-3-small.
    Uses 0 MB of server RAM, eliminating all OOM errors on Render/Railway free tiers.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        try:
            logger.info(f"Initializing cloud API embedding model: {model_name}")
            self.embedding_model = OpenAIEmbeddings(
                model=model_name,
                api_key=OPENAI_API_KEY,
            )
            logger.info("Cloud API embedding model initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise CustomException(e)

    def get_embedding(self):
        return self.embedding_model


if __name__ == "__main__":
    embedding = Embedding(model_name=EMBEDDING_MODEL)
    model = embedding.get_embedding()
    print("Embedding model initialized successfully.")