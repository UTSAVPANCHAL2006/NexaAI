from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from langchain_qdrant import QdrantVectorStore

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)


class QdrantDB:

    def __init__(self, qdrant_url: str, collection_name: str, vector_size: int, api_key: str = None):
        try:
            self.qdrant_url = qdrant_url
            self.api_key = api_key
            self.collection_name = collection_name
            self.vector_size = vector_size

            logger.info("Connecting to Qdrant...")

            self.client = QdrantClient(url=self.qdrant_url, api_key=self.api_key)

            logger.info("Connected successfully.")

        except Exception as e:
            logger.error("Failed to connect to Qdrant.")
            raise CustomException(e)

    def collection_exists_with_data(self) -> bool:
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.collection_name not in collections:
                return False
            count = self.client.count(collection_name=self.collection_name).count
            return count > 0
        except Exception:
            return False

    def create_collection(self):
        try:
            collections = [c.name for c in self.client.get_collections().collections]

            if self.collection_name not in collections:
                logger.info(f"Creating collection '{self.collection_name}'...")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
                )
                logger.info("Collection created.")
            else:
                logger.info("Collection already exists.")

        except Exception as e:
            logger.error("Failed to create collection.")
            raise CustomException(e)

    def upload_document(self, documents, embedding_model):
        try:
            if not documents:
                raise ValueError("No documents to upload.")

            logger.info(f"Uploading {len(documents)} documents to Qdrant...")

            vector_store = QdrantVectorStore.from_documents(
                documents=documents,
                embedding=embedding_model,
                url=self.qdrant_url,
                api_key=self.api_key,
                collection_name=self.collection_name,
            )

            logger.info("Documents uploaded successfully.")
            return vector_store

        except Exception as e:
            logger.error("Failed to upload documents.")
            raise CustomException(e)
