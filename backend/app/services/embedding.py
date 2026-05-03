import os
from functools import lru_cache
from langchain_core.embeddings import DeterministicFakeEmbedding

VECTOR_SIZE = int(os.getenv("VERTOR_SIZE", 768))


@lru_cache(maxsize=1)
def get_embedding_service():
    return DeterministicFakeEmbedding(size=VECTOR_SIZE)
