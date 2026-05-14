from functools import lru_cache
from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .job_queue import JobQueueConfig
from .middleware import MiddlewareConfig
from .database import DatabaseConfig

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    middleware: MiddlewareConfig = Field(default_factory=MiddlewareConfig)

    @computed_field
    @property
    def job_queue(self) -> JobQueueConfig:
        return JobQueueConfig()

    @computed_field
    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig()


@lru_cache
def get_settings() -> Settings:
    return Settings()
