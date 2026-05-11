from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Central settings; extend with new fields as the app grows."""

    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL (e.g. postgresql+psycopg://...)",
    )

    vector_embedding_dimension: PositiveInt = Field(
        ...,
        description="Embedding vector size for the PGVector store",
    )


@lru_cache
def get_settings() -> Settings:
    # Values come from environment / `.env`; pyright cannot see env at analysis time.
    return Settings()  # pyright: ignore[reportCallIssue]

