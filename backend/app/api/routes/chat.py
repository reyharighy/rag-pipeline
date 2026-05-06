import json
import logging
import uuid
from typing import Any, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph.state import CompiledStateGraph
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent import get_initial_state, State, Context
from app.services import get_chat_history_service

router = APIRouter()
logger = logging.getLogger("uvicorn.error")


class ChatAgentRequest(BaseModel):
    chat_input: str
    session_id: str | None = Field(default=None)


def _resolve_session_id(raw: str | None) -> str:
    if raw and str(raw).strip():
        try:
            uuid.UUID(str(raw).strip())

            return str(raw).strip()
        except ValueError:
            pass

    return str(uuid.uuid4())


def _flatten_langchain_message_content(
    content: Any,
    *,
    kind: Literal["human", "ai"],
) -> str | None:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text")

                if isinstance(t, str):
                    parts.append(t)

        if not parts:
            return None if kind == "ai" else ""

        return "".join(parts)

    if content is None:
        return None if kind == "ai" else ""

    return str(content)


def _text_from_human(msg: HumanMessage) -> str:
    out = _flatten_langchain_message_content(msg.content, kind="human")

    return "" if out is None else out


def _content_from_ai_message(msg: AIMessage) -> str | None:
    return _flatten_langchain_message_content(msg.content, kind="ai")


def _assistant_content_from_response_update(update: dict[str, Any]) -> str | None:
    payload = update.get("response")

    if not isinstance(payload, dict):
        return None

    msg = payload.get("messages")

    if msg is None:
        return None

    if isinstance(msg, AIMessage):
        return _content_from_ai_message(msg)

    if isinstance(msg, list):
        for item in reversed(msg):
            if isinstance(item, AIMessage):
                return _content_from_ai_message(item)
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


def _history_messages_for_api(messages: list[BaseMessage]) -> list[dict[str, str]]:
    """Serialize LangChain messages to JSON for the chat UI (human / ai only)."""
    out: list[dict[str, str]] = []

    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": _text_from_human(m)})
        elif isinstance(m, AIMessage):
            out.append(
                {
                    "role": "assistant",
                    "content": _content_from_ai_message(m) or "",
                }
            )

    return out


@router.get("/chat/history")
def chat_history(session_id: str = Query(..., min_length=1)):
    try:
        uuid.UUID(session_id.strip())
    except ValueError as e:
        raise HTTPException(status_code=422, detail="session_id must be a UUID") from e

    try:
        history = get_chat_history_service(session_id.strip())
        stored = history.get_messages()
    except Exception:
        raise HTTPException(
            status_code=500, detail="Failed to load chat history"
        ) from None

    return {"messages": _history_messages_for_api(stored)}


def event_generator(
    graph: CompiledStateGraph[State],
    state: State,
    context: Context,
    *,
    chat_input: str,
    session_id: str,
):
    assistant_text: str | None = None

    try:
        for event in graph.stream(state, context=context, stream_mode="updates"):  # type: ignore[arg-type]
            if isinstance(event, dict) and "response" in event:
                extracted = _assistant_content_from_response_update(event)

                if extracted is not None:
                    assistant_text = extracted

            encoded_event = jsonable_encoder(event)

            payload = json.dumps({"type": "update", "data": encoded_event})

            yield f"{payload}\n\n"

        if assistant_text is not None:
            history = get_chat_history_service(session_id)

            history.add_messages(
                [
                    HumanMessage(content=chat_input),
                    AIMessage(content=assistant_text),
                ]
            )

        yield json.dumps({"type": "complete"}) + "\n\n"

    except Exception as e:
        payload = json.dumps({"type": "update", "data": str(e)})

        yield f"{payload}\n\n"


@router.post("/chat")
def chat_agent(request: Request, chat_agent_request: ChatAgentRequest):
    graph: CompiledStateGraph[State] = request.app.state.graph
    session_id = _resolve_session_id(chat_agent_request.session_id)
    graph_state = get_initial_state(chat_agent_request.chat_input)

    try:
        prior_messages = get_chat_history_service(session_id).get_messages()
    except Exception:
        logger.exception("Failed to load chat history for session %s", session_id)
        prior_messages = []

    graph_context = Context(history_messages=prior_messages)

    def generator():
        payload = json.dumps({"type": "session", "data": {"session_id": session_id}})

        yield f"{payload}\n\n"

        yield from event_generator(
            graph,
            state=graph_state,
            context=graph_context,
            chat_input=chat_agent_request.chat_input,
            session_id=session_id,
        )

    return StreamingResponse(generator(), media_type="text/event-stream")
