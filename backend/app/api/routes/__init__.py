from .chat import router as chat_endpoint
from .health import router as health_endpoint
from .prompt_templates import router as prompt_templates_endpoint
from .upload import router as upload_endpoint

__all__ = [
    "chat_endpoint",
    "health_endpoint",
    "prompt_templates_endpoint",
    "upload_endpoint",
]
