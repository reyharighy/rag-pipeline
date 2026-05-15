import os
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, computed_field

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


Model = Annotated[str, BeforeValidator(parse_vector_embedding_model)]
RawDimension = Annotated[str, BeforeValidator(parse_vector_embedding_dimension)]


class EmbeddingConfig(BaseModel):
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

    @computed_field
    @property
    def dimension(self) -> int:
        return int(self.raw_dimension)
