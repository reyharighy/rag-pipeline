import os
import logging
from functools import lru_cache
from langchain_postgres import PGEngine, PGVectorStore, PostgresChatMessageHistory
from sqlalchemy.exc import ProgrammingError
import psycopg
from psycopg.errors import DuplicateTable

from .embedding import get_embedding_service

logger = logging.getLogger("uvicorn.error")

DATABASE_URL = os.getenv("DATABASE_URL", None)

if DATABASE_URL is None:
    raise ValueError("'DATABASE_URL' is not found")

VECTOR_EMBEDDING_DIMENSION_RAW = os.getenv("VECTOR_EMBEDDING_DIMENSION")

if (
    VECTOR_EMBEDDING_DIMENSION_RAW is None
    or str(VECTOR_EMBEDDING_DIMENSION_RAW).strip() == ""
):
    raise ValueError("'VECTOR_EMBEDDING_DIMENSION' is not found")

try:
    VECTOR_EMBEDDING_DIMENSION = int(VECTOR_EMBEDDING_DIMENSION_RAW)
except ValueError as e:
    raise ValueError("'VECTOR_EMBEDDING_DIMENSION' must be an integer") from e

if VECTOR_EMBEDDING_DIMENSION <= 0:
    raise ValueError("'VECTOR_EMBEDDING_DIMENSION' must be positive")


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


def _database_url_for_psycopg(url: str) -> str:
    for prefix in ("postgresql+psycopg://",):
        if url.startswith(prefix):
            return f"postgresql://{url[len(prefix) :]}"

    return url


_db_conn = psycopg.connect(_database_url_for_psycopg(DATABASE_URL))

CHAT_MESSAGE_HISTORIES_TABLE_NAME = "chat_message_histories"
VECTOR_STORE_TABLE_NAME = "documents"


@lru_cache(maxsize=1)
def _get_db_engine():
    return PGEngine.from_connection_string(str(DATABASE_URL))


def init_tables_if_not_exists():
    try:
        PostgresChatMessageHistory.create_tables(
            _db_conn, CHAT_MESSAGE_HISTORIES_TABLE_NAME
        )

        logger.info(
            "Chat message history table '%s' is ready (CREATE IF NOT EXISTS).",
            CHAT_MESSAGE_HISTORIES_TABLE_NAME,
        )
    except ProgrammingError:
        raise ValueError(
            f"Failed to create table '{CHAT_MESSAGE_HISTORIES_TABLE_NAME}'"
        )

    try:
        _get_db_engine().init_vectorstore_table(
            table_name=VECTOR_STORE_TABLE_NAME,
            vector_size=VECTOR_EMBEDDING_DIMENSION,
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


def get_chat_history_service(session_id: str) -> PostgresChatMessageHistory:
    return PostgresChatMessageHistory(
        CHAT_MESSAGE_HISTORIES_TABLE_NAME,
        session_id,
        sync_connection=_db_conn,
    )


def get_vector_db_service():
    return PGVectorStore.create_sync(
        engine=_get_db_engine(),
        table_name=VECTOR_STORE_TABLE_NAME,
        embedding_service=get_embedding_service(),
    )
