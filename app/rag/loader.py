import json

from pathlib import Path
from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document

logger = get_logger(__name__)


class Loader:

    def __init__(self, kb_path: str, resolved_path: str):
        self.kb_path = kb_path
        self.resolved_path = resolved_path

    def load_documents(self):
        try:

            logger.info(f"Loading MarkDown Documents From {self.kb_path}")

            loader = DirectoryLoader(
                path=str(self.kb_path),
                glob="*.md",
                loader_cls=TextLoader,
                loader_kwargs={"encoding": "utf-8"},
            )

            docs = loader.load()

            for doc in docs:
                doc.metadata["type"] = "policy"
                doc.metadata["source"] = Path(doc.metadata["source"]).name

            logger.info(f"Loaded {len(docs)} markdown documents.")

            return docs

        except Exception as e:
            logger.error("Error To Load MarkDown Data")
            raise CustomException("Failed To Load Data") from e

    def load_resolved_tickets(self):
        try:

            logger.info(f"Loading The Resolved Data {self.resolved_path}")

            with open(self.resolved_path, "r", encoding="utf-8") as file:
                tickets = json.load(file)

            documents = []

            for ticket in tickets:

                case_id = ticket.get("case_id") or ticket.get("ticket_id")
                account_id = ticket.get("account_id") or ticket.get("order_id")
                content = (
                    f"Case ID: {case_id}\n"
                    f"Account ID: {account_id}\n"
                    f"Category: {ticket['category']}\n"
                    f"Urgency: {ticket['urgency']}\n"
                    f"Sentiment: {ticket['sentiment']}\n"
                    f"Tags: {', '.join(ticket['tags'])}\n"
                    f"Issue: {ticket['issue']}\n\n"
                    f"Resolution: {ticket['resolution']}"
                )

                document = Document(
                    page_content=content,
                    metadata={
                        "source": "resolved_tickets.json",
                        "type": "resolved_ticket",
                        "case_id": case_id,
                        "account_id": account_id,
                        "category": ticket["category"],
                        "urgency": ticket["urgency"],
                        "sentiment": ticket["sentiment"],
                        "tags": ticket["tags"],
                    },
                )

                documents.append(document)

            logger.info(f"Loaded {len(documents)} resolved tickets.")

            return documents

        except Exception as e:
            logger.error("Failed to load resolved tickets.")
            raise CustomException(e)

    def load_all_documents(self):
        try:

            policy_docs = self.load_documents()

            ticket_docs = self.load_resolved_tickets()

            all_docs = policy_docs + ticket_docs

            logger.info(f"Total documents loaded: {len(all_docs)}")

            return all_docs

        except Exception as e:
            logger.error("Failed to load all documents.")
            raise CustomException(e)
