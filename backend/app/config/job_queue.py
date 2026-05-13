import os
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field


def default_redis_url() -> str:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    if redis_url is None:
        raise ValueError("REDIS_URL is not set")

    return redis_url


def parse_embed_job_result_ttl(value: Any) -> int:
    if value is None:
        return -1

    if isinstance(value, int):
        return value

    raw = str(value).strip().lower()

    if raw in ("", "-1", "forever"):
        return -1

    return int(raw)


EmbedJobResultTtl = Annotated[int, BeforeValidator(parse_embed_job_result_ttl)]


class JobQueueConfig(BaseModel):
    redis_url: str = Field(
        default_factory=default_redis_url,
        description="Redis URL for RQ (env: REDIS_URL).",
    )

    embed_job_result_ttl: EmbedJobResultTtl = Field(
        default=-1,
        description="RQ job result TTL in seconds (env: EMBED_JOB_RESULT_TTL).",
    )
