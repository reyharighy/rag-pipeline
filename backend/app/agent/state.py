from typing import Any
from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState


def get_initial_state(chat_input: str):
    return State(
        messages=[HumanMessage(content=chat_input)],
        state=None,
        runtime=None,
    )


class State(MessagesState):
    state: Any | None
    runtime: Any | None
