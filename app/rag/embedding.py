from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from app.config.config import EMBEDDING_MODEL

logger = get_logger(__name__)


class Embedding:
    """Lightweight ONNX-powered embedding model using FastEmbed.
    Consumes ~50MB RAM instead of ~550MB PyTorch RAM, ideal for cloud hosting.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        try:
            logger.info(f"Loading FastEmbed model: {model_name}")
            self.embedding_model = FastEmbedEmbeddings(model_name=model_name)
            logger.info("FastEmbed model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load FastEmbed model: {e}")
            raise CustomException(e)

    def get_embedding(self):
        return self.embedding_model


if __name__ == "__main__":
    embedding = Embedding(model_name=EMBEDDING_MODEL)
    model = embedding.get_embedding()
    print("Embedding model initialized successfully.")