import json
import logging
import uuid
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from fastapi import APIRouter, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import get_initial_state, State, Context
from app.database.tables import ChatMessageHistories
from app.utils import content_from_ai_message, text_from_human_message

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


def _resolve_session_id(raw: str | None) -> str:
    if raw and str(raw).strip():
        try:
            uuid.UUID(str(raw).strip())
        except ValueError:
            pass
        else:
            return str(raw).strip()

    return str(uuid.uuid4())


def _history_messages_for_api_response(
    messages: list[BaseMessage],
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []

    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": text_from_human_message(m)})
        elif isinstance(m, AIMessage):
            content = content_from_ai_message(m)

            if content is None:
                continue

            out.append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

    return out


class ChatHistoryResponse(BaseModel):
    messages: list[dict[str, str]]


@router.get("/chat/history")
def chat_history(session_id: str = Query(..., min_length=1)) -> ChatHistoryResponse:
    session_id = _resolve_session_id(session_id)

    chat_message_histories = ChatMessageHistories(session_id)
    stored_messages = chat_message_histories.get()

    return ChatHistoryResponse(
        messages=_history_messages_for_api_response(stored_messages)
    )


def _assistant_content_from_response_update(update: dict[str, Any]) -> str | None:
    payload = update.get("response")

    if not isinstance(payload, dict):
        return None

    msg = payload.get("messages")

    if msg is None:
        return None

    if isinstance(msg, AIMessage):
        return content_from_ai_message(msg)

    if isinstance(msg, list):
        for item in reversed(msg):
            if isinstance(item, AIMessage):
                return content_from_ai_message(item)
            if isinstance(item, dict) and item.get("type") == "ai":
                c = item.get("content")

                if isinstance(c, str):
                    return c

        return None

    if isinstance(msg, dict):
        c = msg.get("content")

        if isinstance(c, str):
            return c

    return None


class ChatAgentRequest(BaseModel):
    chat_input: str
    session_id: str | None = Field(default=None, min_length=1)


@router.post("/chat")
def chat_agent(
    request: Request, chat_agent_request: ChatAgentRequest
) -> StreamingResponse:
    session_id = _resolve_session_id(chat_agent_request.session_id)

    chat_message_histories = ChatMessageHistories(session_id)
    stored_messages = chat_message_histories.get()

    graph: CompiledStateGraph[State] = request.app.state.graph
    graph_state = get_initial_state(chat_agent_request.chat_input)
    graph_context = Context(history_messages=stored_messages)

    def generator():
        payload = json.dumps({"type": "session", "data": {"session_id": session_id}})

        yield f"{payload}\n\n"

        def event_generator():
            assistant_text: str | None = None

            try:
                for event in graph.stream(
                    graph_state,
                    context=graph_context,  # type: ignore[arg-type]
                    stream_mode="updates",
                ):
                    if isinstance(event, dict) and "response" in event:
                        extracted = _assistant_content_from_response_update(event)

                        if extracted is not None:
                            assistant_text = extracted

                    encoded_event = jsonable_encoder(event)

                    payload = json.dumps({"type": "update", "data": encoded_event})

                    yield f"{payload}\n\n"

                yield json.dumps({"type": "complete"}) + "\n\n"

            except Exception as e:
                payload = json.dumps({"type": "update", "data": str(e)})

                yield f"{payload}\n\n"
            else:
                if assistant_text is not None:
                    chat_message_histories = ChatMessageHistories(session_id)

                    chat_message_histories.add(
                        [
                            HumanMessage(content=chat_agent_request.chat_input),
                            AIMessage(content=assistant_text),
                        ]
                    )

        yield from event_generator()

    return StreamingResponse(generator(), media_type="text/event-stream")
