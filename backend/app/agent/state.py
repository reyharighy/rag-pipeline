from langchain_core.messages import HumanMessage
from langgraph.graph import MessagesState


def get_initial_state(chat_input: str):
    return State(
        messages=[HumanMessage(content=chat_input)],
        relevant_docs=None,
        refined_query=None,
    )


class State(MessagesState):
    relevant_docs: list | None
    refined_query: str | None
