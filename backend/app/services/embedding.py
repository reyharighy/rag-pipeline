import os
from functools import lru_cache
from langchain_cohere import CohereEmbeddings

from app.config import get_settings

COHERE_API_KEY = os.getenv("COHERE_API_KEY", None)

if COHERE_API_KEY is None:
    raise ValueError("'COHERE_API_KEY' is not found")

_embedding_cfg = get_settings().embedding


@lru_cache(maxsize=1)
def get_embedding_service():
    return CohereEmbeddings(
        cohere_api_key=COHERE_API_KEY,
        model=_embedding_cfg.model,
    )  # type: ignore[report-call-issue]
