from contextlib import asynccontextmanager
from fastapi import FastAPI

from .routes import routers
from app.workers.vector_store import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)
