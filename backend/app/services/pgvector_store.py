import os
from functools import lru_cache
from langchain_postgres import PGEngine, PGVectorStore
from sqlalchemy.exc import ProgrammingError

from . import get_embedding

VECTORDB_URL = os.getenv("VECTORDB_URL", "")
VECTOR_SIZE = int(os.getenv("VERTOR_SIZE", 768))

@lru_cache(maxsize=1)
def get_engine():
    return PGEngine.from_connection_string(VECTORDB_URL)

def get_vector_store():
    return PGVectorStore.create_sync(
        engine=get_engine(),
        table_name="documents",
        embedding_service=get_embedding(),
    )

def init_db():
    try:
        get_engine().init_vectorstore_table(
            table_name="documents",
            vector_size=VECTOR_SIZE,
        )
    except ProgrammingError:
        pass
