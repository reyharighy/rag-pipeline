from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState


def get_initial_state(chat_input: str):
    return State(
        messages=[HumanMessage(content=chat_input)],
    )


class State(MessagesState):
    pass
