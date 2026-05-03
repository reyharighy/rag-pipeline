from time import sleep
from langgraph.runtime import Runtime

from typing import Any
from .runtime import Context
from .state import State

def first_node(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    sleep(5)

    return {
        "messages": state.get("messages"),
        "state": state,
        "runtime": runtime,
    }
