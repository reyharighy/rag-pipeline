from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .database import DatabaseConfig
from .embedding import EmbeddingConfig
from .job_queue import JobQueueConfig
from .middleware import MiddlewareConfig

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    @computed_field
    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig()

    @computed_field
    @property
    def embedding(self) -> EmbeddingConfig:
        return EmbeddingConfig()

    @computed_field
    @property
    def job_queue(self) -> JobQueueConfig:
        return JobQueueConfig()

    middleware: MiddlewareConfig = Field(default_factory=MiddlewareConfig)


@lru_cache
def get_settings() -> Settings:
    return Settings()
