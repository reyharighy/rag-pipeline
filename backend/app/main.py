from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import routers
from app.services import init_vector_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_vector_db()
    yield


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)
