from pydantic import BaseModel, Field


def _default_cors_allowed_origins() -> list[str]:
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ]

def _default_dev_origin_regex() -> str:
    return r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"


class MiddlewareConfig(BaseModel):
    allowed_origins: list[str] = Field(
        default_factory=_default_cors_allowed_origins,
        description="Explicit origins passed to CORSMiddleware allow_origins.",
    )

    dev_origin_regex: str = Field(
        default_factory=_default_dev_origin_regex,
        description="Regex passed to CORSMiddleware allow_origin_regex (dev hosts/ports).",
    )
