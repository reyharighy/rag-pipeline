import logging

from sqlalchemy.exc import ProgrammingError

from .base import Table
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
_database_cfg = get_settings().database
_embedding_cfg = get_settings().embedding

VECTOR_STORE_TABLE_NAME = "documents"

class VectorDocument(Table):
    def __init__(self, id: str):
        self.id = id

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
