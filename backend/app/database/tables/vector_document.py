import logging
from typing import Any, Optional

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_postgres import PGVectorStore
from sqlalchemy.exc import ProgrammingError

from .base import Table
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
_database_cfg = get_settings().database
_embedding_cfg = get_settings().embedding

VECTOR_STORE_TABLE_NAME = "documents"

class VectorDocument(Table):
    def __init__(self, embedding_service: Embeddings):
        self.service = PGVectorStore.create_sync(
            engine=_database_cfg.engine,
            table_name=VECTOR_STORE_TABLE_NAME,
            embedding_service=embedding_service,
        )

    @staticmethod
    def create_table() -> None:
        try:
            _database_cfg.engine.init_vectorstore_table(
                table_name=VECTOR_STORE_TABLE_NAME,
                vector_size=_embedding_cfg.dimension,
            )
        except ProgrammingError as e:
            if Table.is_duplicate_table_error(e):
                logger.info(
                    "Vector store table '%s' already exists; skipping create.",
                    VECTOR_STORE_TABLE_NAME,
                )

                return

            raise ValueError(
                "Failed to create table '%s': %s.", VECTOR_STORE_TABLE_NAME, e
            ) from e
        except Exception as e:
            raise ValueError(
                "Unexpected error while creating table '%s': %s.",
                VECTOR_STORE_TABLE_NAME,
                e,
            ) from e
        else:
            logger.info(
                "Vector store table '%s' is ready.",
                VECTOR_STORE_TABLE_NAME,
            )

    def add(self, **kwargs: Any) -> None:
        entry = kwargs.get("entry", None)

        if entry is None:
            raise ValueError("entry is required")

        if isinstance(entry, list) and not all(
            isinstance(r, Document) for r in entry
        ):
            raise ValueError("entry is a list that contains non-BaseMessage items")

        if not isinstance(entry, list) and not isinstance(entry, Document):
            raise ValueError("entry is not a list or Document")

        if isinstance(entry, Document):
            entry = [entry]

        self.service.add_documents(entry)

    def get(self, **kwargs: Any) -> Any:
        query = kwargs.get("query", None)

        if query is not None:
            raise NotImplementedError("query is not implemented")

        raise NotImplementedError("VectorDocument does not support getting documents")

    def similarity_search(self, **kwargs: Any) -> Any:
        query = kwargs.get("query", None)

        if query is None:
            raise ValueError("query is required")

        top_k = kwargs.get("top_k", 8)

        if not isinstance(top_k, int):
            raise ValueError("top_k must be an integer")

        return self.service.similarity_search(query, top_k)
