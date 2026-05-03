from .health import router as health_endpoint
from .upload import router as upload_endpoint

__all__ = [
    "health_endpoint",
    "upload_endpoint",
]
