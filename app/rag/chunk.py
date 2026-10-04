from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)


class Chunker:

    def __init__(self, chunk_size: int, chunk_overlap: int):

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

    def create_text_chunks(self, documents):
        try:

            if not documents:
                raise ValueError("No documents found for chunking.")

            logger.info(f"Splitting {len(documents)} documents into chunks...")

            chunks = self.text_splitter.split_documents(documents)

            logger.info(f"Generated {len(chunks)} chunks.")

            return chunks

        except Exception as e:
            logger.exception("Failed to create document chunks.")
            raise CustomException(e)
