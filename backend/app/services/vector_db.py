import os
from functools import lru_cache
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.exc import ProgrammingError

from app.services import get_embedding_service

VECTORDB_URL = os.getenv("VECTORDB_URL", None)

if VECTORDB_URL is None:
    print("'VECTORDB_URL' is not found")

VECTOR_SIZE = os.getenv("VECTOR_SIZE", 512)

if VECTOR_SIZE is 0:
    print("'VECTOR_SIZE' is not found")


@lru_cache(maxsize=1)
def get_vector_db_engine():
    return PGEngine.from_connection_string(str(VECTORDB_URL))


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
            vector_size=int(VECTOR_SIZE),
        )
    except ProgrammingError:
        pass
