from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import Graph
from app.api import routers
from app.config import get_settings
from app.services import init_tables_if_not_exists
from app.database.tables import ChatMessageHistories


@asynccontextmanager
async def lifespan(app: FastAPI):
    ChatMessageHistories.create_table()
    init_tables_if_not_exists()
    app.state.graph = Graph().build_graph()

    yield


app = FastAPI(lifespan=lifespan)

_middleware_settings = get_settings().middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=_middleware_settings.allowed_origins,
    allow_origin_regex=_middleware_settings.dev_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)
