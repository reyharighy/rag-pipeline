from .routes import health_endpoint, upload_endpoint

routers = [
    health_endpoint,
    upload_endpoint,
]

__all__ = [
    "routers",
]
