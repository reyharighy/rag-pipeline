from typing import Any
from langchain_core.messages import AnyMessage, HumanMessage
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
    system_prompt = "Based on the information below, answer the user question:\n"
    context_prompt = state["relevant_docs"]

    system_message = SystemMessage(system_prompt + str(context_prompt))
    llm_input: list[AnyMessage] = [system_message]
    llm_input.extend([HumanMessage(str(state["messages"][-1].content))])

    llm = get_language_model(model="openai/gpt-oss-120b")
    response = llm.invoke(llm_input)

    return {
        "messages": response,
    }
