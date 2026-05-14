import os
from functools import lru_cache
from typing import Annotated

import psycopg
from psycopg.rows import TupleRow
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, computed_field
from langchain_postgres import PGEngine


def parse_username(value: str) -> str:
    if value.strip() == "":
        raise ValueError("DATABASE_USERNAME is not set")

    return value


def parse_password(value: str) -> str:
    if value.strip() == "":
        raise ValueError("DATABASE_PASSWORD is not set")

    return value


def parse_database_name(value: str) -> str:
    if value.strip() == "":
        raise ValueError("DATABASE_NAME is not set")

    return value


@lru_cache(maxsize=1)
def _get_engine(database_url: str) -> PGEngine:
    return PGEngine.from_connection_string(database_url)


@lru_cache(maxsize=1)
def _get_psycopg_connection(url: str) -> psycopg.Connection[TupleRow]:
    for prefix in ("postgresql+psycopg://",):
        if url.startswith(prefix):
            return psycopg.connect(f"postgresql://{url[len(prefix) :]}")

    return psycopg.connect(url)


UserName = Annotated[str, BeforeValidator(parse_username)]
Password = Annotated[str, BeforeValidator(parse_password)]
DatabaseName = Annotated[str, BeforeValidator(parse_database_name)]


class DatabaseConfig(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    username: UserName = Field(
        default_factory=lambda: os.getenv("DATABASE_USERNAME", ""),
        validate_default=True,
        description="Username for the database",
    )

    password: Password = Field(
        default_factory=lambda: os.getenv("DATABASE_PASSWORD", ""),
        validate_default=True,
        description="Password for the database",
    )

    name: DatabaseName = Field(
        default_factory=lambda: os.getenv("DATABASE_NAME", ""),
        validate_default=True,
        description="Name of the database",
    )

    @computed_field
    @property
    def url(self) -> str:
        return f"postgresql+psycopg://{self.username}:{self.password}@database:5432/{self.name}"

    @computed_field
    @property
    def engine(self) -> PGEngine:
        return _get_engine(self.url)

    @computed_field
    @property
    def psycopg_connection(self) -> psycopg.Connection[TupleRow]:
        return _get_psycopg_connection(self.url)
