import os
from typing import Annotated

from functools import lru_cache
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field
from langchain_cohere import CohereEmbeddings
from langchain_core.embeddings import Embeddings

ALLOWED_VECTOR_EMBEDDING_DIMENSION_DEFAULT = [
    384,
    768,
    1024,
    1536,
    2048,
    3072,
]


def parse_vector_embedding_model(value: str) -> str:
    if value.strip() == "":
        raise ValueError("VECTOR_EMBEDDING_MODEL is not set")

    return value.strip()


def parse_vector_embedding_dimension(value: str) -> str:
    if value.strip() == "":
        return str(ALLOWED_VECTOR_EMBEDDING_DIMENSION_DEFAULT[2])

    if int(value.strip()) in ALLOWED_VECTOR_EMBEDDING_DIMENSION_DEFAULT:
        return value.strip()

    raise ValueError(
        "VECTOR_EMBEDDING_DIMENSION must be one of the following: "
        + ", ".join(map(str, ALLOWED_VECTOR_EMBEDDING_DIMENSION_DEFAULT))
    )

def parse_api_key(value: str) -> str:
    if value.strip() == "":
        raise ValueError("COHERE_API_KEY is not set")

    return value.strip()

@lru_cache(maxsize=1)
def _get_embedding_service(api_key: "ApiKey", model: "Model") -> Embeddings:
    return CohereEmbeddings(
        cohere_api_key=api_key,
        model=model,
    )

Model = Annotated[str, BeforeValidator(parse_vector_embedding_model)]
RawDimension = Annotated[str, BeforeValidator(parse_vector_embedding_dimension)]
ApiKey = Annotated[str, BeforeValidator(parse_api_key)]

class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    model: Model = Field(
        default_factory=lambda: os.getenv("VECTOR_EMBEDDING_MODEL", ""),
        validate_default=True,
        description="Model of the embedding service",
    )

    raw_dimension: RawDimension = Field(
        default_factory=lambda: os.getenv("EMBEDDING_DIMENSION", ""),
        validate_default=True,
        description="Dimension of stored embedding vectors",
    )

    api_key: ApiKey = Field(
        default_factory=lambda: os.getenv("COHERE_API_KEY", ""),
        validate_default=True,
        description="API key of the embedding service",
    )

    @computed_field
    @property
    def dimension(self) -> int:
        return int(self.raw_dimension)

    @computed_field
    @property
    def service(self) -> Embeddings:
        return _get_embedding_service(self.api_key, self.model)
