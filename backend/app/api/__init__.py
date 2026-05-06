from .routes import (
    chat_endpoint,
    health_endpoint,
    prompt_templates_endpoint,
    upload_endpoint,
)

routers = [
    chat_endpoint,
    health_endpoint,
    prompt_templates_endpoint,
    upload_endpoint,
]

__all__ = [
    "routers",
]
