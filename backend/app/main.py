from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import routers, init_vector_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_vector_db()
    yield


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)
