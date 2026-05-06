"""Plain-text helpers for LangChain messages and documents (shared by API and eval)."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any, Literal

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def _flatten_langchain_message_content(
    content: Any,
    *,
    kind: Literal["human", "ai"],
) -> str | None:
    """Normalize LangChain message content (string or multimodal blocks) to text."""
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


def text_from_human_message(msg: HumanMessage) -> str:
    out = _flatten_langchain_message_content(msg.content, kind="human")

    return "" if out is None else out


def content_from_ai_message(msg: AIMessage) -> str | None:
    return _flatten_langchain_message_content(msg.content, kind="ai")


def last_assistant_text(messages: Sequence[BaseMessage]) -> str:
    """Return text from the last AIMessage, stripped. Raises if none."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return (content_from_ai_message(msg) or "").strip()

    raise ValueError("No AIMessage found in message list")


def texts_from_documents(docs: Iterable[Document] | None) -> list[str]:
    """Non-empty stripped page_content strings from LangChain documents."""
    if not docs:
        return []

    out: list[str] = []

    for d in docs:
        text = (d.page_content or "").strip()

        if text:
            out.append(text)

    return out
