import logging
from typing import Any, Optional

from langchain_core.messages import BaseMessage
from langchain_postgres import PostgresChatMessageHistory
from sqlalchemy.exc import ProgrammingError

from .base import Table
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")
_database_cfg = get_settings().database

CHAT_MESSAGE_HISTORIES_TABLE_NAME = "chat_message_histories"


class ChatMessageHistories(Table):
    def __init__(self, session_id: str):
        self.service = PostgresChatMessageHistory(
            CHAT_MESSAGE_HISTORIES_TABLE_NAME,
            session_id,
            sync_connection=_database_cfg.psycopg_connection,
        )

    @staticmethod
    def create_table() -> None:
        try:
            PostgresChatMessageHistory.create_tables(
                _database_cfg.psycopg_connection,
                CHAT_MESSAGE_HISTORIES_TABLE_NAME,
            )
        except ProgrammingError as e:
            if Table.is_duplicate_table_error(e):
                logger.info(
                    "Table '%s' already exists; skipping create.",
                    CHAT_MESSAGE_HISTORIES_TABLE_NAME,
                )

                return

            raise ValueError(
                "Failed to create table '%s': %s.", CHAT_MESSAGE_HISTORIES_TABLE_NAME, e
            ) from e
        except Exception as e:
            raise ValueError(
                "Unexpected error while creating table '%s': %s.",
                CHAT_MESSAGE_HISTORIES_TABLE_NAME,
                e,
            ) from e
        else:
            logger.info(
                "Chat message history table '%s' is ready.",
                CHAT_MESSAGE_HISTORIES_TABLE_NAME,
            )

    def add(self, entry: list[BaseMessage] | BaseMessage) -> None:
        if isinstance(entry, list) and not all(
            isinstance(r, BaseMessage) for r in entry
        ):
            raise ValueError("entry is a list that contains non-BaseMessage items")

        if not isinstance(entry, list) and not isinstance(entry, BaseMessage):
            raise ValueError("entry is a single item that is not a BaseMessage")

        if isinstance(entry, BaseMessage):
            entry = [entry]

        self.service.add_messages(entry)

    def get(self, query: Optional[Any] = None) -> list[BaseMessage]:
        if query is not None:
            raise ValueError("query is not implemented")

        return self.service.get_messages()
