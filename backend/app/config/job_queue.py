import os
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

JOB_QUEUE_RESULT_TTL_DEFAULT = -1


def parse_url(value: str) -> str:
    if value.strip() == "":
        raise ValueError("JOB_QUEUE_URL is not set")

    return value


def parse_result_ttl(value: str) -> int:
    if value.strip() == "" or value.strip() == "-1":
        return JOB_QUEUE_RESULT_TTL_DEFAULT

    try:
        int_value = int(value)

        if int_value < 0:
            raise ValueError("JOB_QUEUE_RESULT_TTL must be a positive integer")

        return int_value
    except ValueError:
        raise ValueError("JOB_QUEUE_RESULT_TTL must be an integer")


JobQueueURL = Annotated[str, BeforeValidator(parse_url)]
JobQueueResultTtl = Annotated[int, BeforeValidator(parse_result_ttl)]


class JobQueueConfig(BaseModel):
    url: JobQueueURL = Field(
        default_factory=lambda: os.getenv("JOB_QUEUE_URL", ""),
        validate_default=True,
        description="URL of the job queue service",
    )

    result_ttl: JobQueueResultTtl = Field(
        default_factory=lambda: os.getenv("JOB_QUEUE_RESULT_TTL", ""),
        validate_default=True,
        description="TTL of the job queue result in seconds (-1 = forever)",
    )
