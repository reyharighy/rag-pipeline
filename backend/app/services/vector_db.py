import os
from functools import lru_cache
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.exc import ProgrammingError

from .embedding import get_embedding_service

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


@lru_cache(maxsize=1)
def get_vector_db_engine():
    return PGEngine.from_connection_string(str(DATABASE_URL))


def get_vector_db_service():
    return PGVectorStore.create_sync(
        engine=get_vector_db_engine(),
        table_name="documents",
        embedding_service=get_embedding_service(),
    )


def init_vector_db():
    try:
        get_vector_db_engine().init_vectorstore_table(
            table_name="documents",
            vector_size=VECTOR_EMBEDDING_DIMENSION,
        )
    except ProgrammingError:
        pass
