from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.agent import Graph
from app.api import routers
from app.services import init_vector_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_vector_db()
    app.state.graph = Graph().build_graph()

    yield


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)
