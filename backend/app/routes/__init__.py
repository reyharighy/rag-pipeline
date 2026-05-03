from .health import router as health_endpoint
from .upload import router as upload_endpoint

routers = [
    health_endpoint,
    upload_endpoint,
]

__all__ = ["routers"]
