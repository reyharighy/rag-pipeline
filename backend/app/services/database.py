import os
import logging
from functools import lru_cache
import uuid
from langchain_postgres import PGEngine, PGVectorStore, PostgresChatMessageHistory
from sqlalchemy.exc import ProgrammingError
import psycopg

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


def database_url_for_psycopg(url: str) -> str:
    for prefix in ("postgresql+psycopg://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix):]

    return url


db_conn = psycopg.connect(database_url_for_psycopg(str(DATABASE_URL)))
session_id = str(uuid.uuid4())

CHAT_MESSAGE_HISTORIES_TABLE_NAME = "chat_message_histories"
VECTOR_STORE_TABLE_NAME = "documents"


@lru_cache(maxsize=1)
def get_db_engine():
    return PGEngine.from_connection_string(str(DATABASE_URL))


def init_tables_if_not_exists():
    try:
        PostgresChatMessageHistory.create_tables(
            db_conn, CHAT_MESSAGE_HISTORIES_TABLE_NAME
        )

        logger.info(f"Created table '{CHAT_MESSAGE_HISTORIES_TABLE_NAME}'")
    except ProgrammingError:
        raise ValueError(
            f"Failed to create table '{CHAT_MESSAGE_HISTORIES_TABLE_NAME}'"
        )

    try:
        get_db_engine().init_vectorstore_table(
            table_name=VECTOR_STORE_TABLE_NAME,
            vector_size=VECTOR_EMBEDDING_DIMENSION,
        )

        logger.info(f"Created table '{VECTOR_STORE_TABLE_NAME}'")
    except ProgrammingError:
        raise ValueError(f"Failed to create table '{VECTOR_STORE_TABLE_NAME}'")


def get_chat_history_service():
    return PostgresChatMessageHistory(
        CHAT_MESSAGE_HISTORIES_TABLE_NAME,
        session_id,
        sync_connection=db_conn,
    )


def get_vector_db_service():
    return PGVectorStore.create_sync(
        engine=get_db_engine(),
        table_name=VECTOR_STORE_TABLE_NAME,
        embedding_service=get_embedding_service(),
    )
