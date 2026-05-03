import os
from functools import lru_cache
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.exc import ProgrammingError

from app.services import get_embedding_service

VECTORDB_URL = os.getenv("VECTORDB_URL", "")
VECTOR_SIZE = int(os.getenv("VERTOR_SIZE", 768))


@lru_cache(maxsize=1)
def get_vector_db_engine():
    return PGEngine.from_connection_string(VECTORDB_URL)


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
            vector_size=VECTOR_SIZE,
        )
    except ProgrammingError:
        pass
