import os
from functools import lru_cache
from langchain_cohere import CohereEmbeddings

COHERE_API_KEY = os.getenv("COHERE_API_KEY", None)

if COHERE_API_KEY is None:
    raise ValueError("'COHERE_API_KEY' is not found")


@lru_cache(maxsize=1)
def get_embedding_service():
    return CohereEmbeddings(                    # type: ignore[report-call-issue]
        cohere_api_key=COHERE_API_KEY,
        model="embed-multilingual-v3.0"
    )
