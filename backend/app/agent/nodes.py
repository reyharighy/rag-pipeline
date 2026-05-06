from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.messages.system import SystemMessage
from langgraph.runtime import Runtime

from app.services import get_language_model, get_vector_db_service

from .runtime import Context
from .state import State


def get_relevant_docs(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    store = get_vector_db_service()
    query = state["messages"][-1]

    relevant_docs = store.similarity_search(str(query.content))

    return {"relevant_docs": relevant_docs}


def response(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    system_message = SystemMessage(
        "You are a helpful assistant. Use the conversation history when relevant. "
        "The final user message may contain labeled sections: retrieved context "
        "(for grounding) and the current request. Answer the current request, "
        "using retrieved context when it applies. "
        "Format every reply as Markdown (e.g. **bold**, lists, `inline code`, "
        "## headings when helpful); plain paragraphs are fine. "
        "Do not wrap the entire answer in a fenced code block unless you are "
        "showing actual code."
    )

    llm_input: list[BaseMessage] = [system_message]
    current_user_message = state["messages"][-1]

    combined_user_content = (
        "The following is a single user turn with two labeled parts.\n\n"
        "--- Retrieved context ---\n"
        f"{str(state['relevant_docs'])}\n\n"
        "--- Current request ---\n"
        f"{str(current_user_message.content)}"
    )

    user_turn = HumanMessage(content=combined_user_content)
    llm_input.extend(runtime.context.history_messages)
    llm_input.append(user_turn)

    llm = get_language_model(model="openai/gpt-oss-120b")
    response = llm.invoke(llm_input)

    return {
        "messages": response,
    }
