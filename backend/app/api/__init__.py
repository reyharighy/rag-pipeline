from .routes import chat_endpoint, health_endpoint, upload_endpoint

routers = [
    chat_endpoint,
    health_endpoint,
    upload_endpoint,
]

__all__ = [
    "routers",
]
