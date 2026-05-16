import os
import logging
from langchain_postgres import PGVectorStore
from sqlalchemy.exc import ProgrammingError
from psycopg.errors import DuplicateTable

from .embedding import get_embedding_service
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
_database_cfg = get_settings().database
_embedding_cfg = get_settings().embedding


def _is_duplicate_table_error(exc: BaseException) -> bool:
    seen: set[int] = set()
    cur: BaseException | None = exc

    while cur is not None and len(seen) < 16:
        if id(cur) in seen:
            break

        seen.add(id(cur))

        if isinstance(cur, DuplicateTable):
            return True

        nxt = getattr(cur, "orig", None)

        if isinstance(nxt, BaseException):
            cur = nxt
            continue

        cur = cur.__cause__

    msg = str(exc).lower()

    return "already exists" in msg and "relation" in msg


VECTOR_STORE_TABLE_NAME = "documents"


def init_tables_if_not_exists():
    try:
        _database_cfg.engine.init_vectorstore_table(
            table_name=VECTOR_STORE_TABLE_NAME,
            vector_size=_embedding_cfg.dimension,
        )

        logger.info(f"Created table '{VECTOR_STORE_TABLE_NAME}'")
    except ProgrammingError as e:
        if _is_duplicate_table_error(e):
            logger.info(
                "Vector store table '%s' already exists; skipping create.",
                VECTOR_STORE_TABLE_NAME,
            )
        else:
            raise ValueError(
                f"Failed to create table '{VECTOR_STORE_TABLE_NAME}'"
            ) from e

    from app.services.prompt_templates import (
        init_prompt_templates_table,
        seed_prompt_templates_if_needed,
    )

    init_prompt_templates_table()
    seed_prompt_templates_if_needed()


def get_vector_db_service():
    return PGVectorStore.create_sync(
        engine=_database_cfg.engine,
        table_name=VECTOR_STORE_TABLE_NAME,
        embedding_service=get_embedding_service(),
    )
