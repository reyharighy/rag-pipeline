from typing import Any
from langgraph.runtime import Runtime

from app.services import get_language_model

from .runtime import Context
from .state import State


def first_node(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    llm = get_language_model(model="openai/gpt-oss-120b")
    response = llm.invoke(state["messages"])

    return {
        "messages": response,
    }
