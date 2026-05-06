import os
from functools import lru_cache
from langchain_cohere import CohereEmbeddings

COHERE_API_KEY = os.getenv("COHERE_API_KEY", None)

if COHERE_API_KEY is None:
    raise ValueError("'COHERE_API_KEY' is not found")

_EMBEDDING_MODEL_RAW = os.getenv("EMBEDDING_MODEL", "embed-multilingual-v3.0").strip()
EMBEDDING_MODEL = _EMBEDDING_MODEL_RAW or "embed-multilingual-v3.0"


@lru_cache(maxsize=1)
def get_embedding_service():
    return CohereEmbeddings(
        cohere_api_key=COHERE_API_KEY,
        model=EMBEDDING_MODEL,
    )  # type: ignore[report-call-issue]
