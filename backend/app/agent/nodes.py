from typing import Any, cast

from langchain_core.messages import BaseMessage
from langchain_core.messages.system import SystemMessage
from langgraph.runtime import Runtime

from app.services import get_language_model, get_vector_db_service, with_retry_exception

from .composer import (
    REFINE_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
    compose_last_human_message_for_node,
)
from .runtime import Context
from .schemas import RefinedRetrievalQuery
from .state import State


def refine_query(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    system_message = SystemMessage(REFINE_SYSTEM_PROMPT.strip())
    llm_input: list[BaseMessage] = [system_message]
    llm_input.extend(runtime.context.history_messages)
    current_user_message = state.get("messages", [])[-1]

    last_message = compose_last_human_message_for_node(
        content=cast(str, current_user_message.content),
    )

    llm_input.extend(last_message)

    base_llm = get_language_model(
        model="openai/gpt-oss-120b",
        reasoning_format="parsed",
        temperature=0,
    )

    llm = with_retry_exception(
        base_llm.with_structured_output(
            schema=RefinedRetrievalQuery,
            method="json_schema",
        )
    )

    lm_output = llm.invoke(llm_input)

    return {"refined_query": cast(RefinedRetrievalQuery, lm_output).refined_query}


def get_relevant_docs(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    store = get_vector_db_service()
    query_text = cast(str, state.get("refined_query") or "").strip()

    if not query_text:
        query_text = cast(str, state["messages"][-1].content)

    relevant_docs = store.similarity_search(cast(str, query_text))

    return {"relevant_docs": relevant_docs}


def response(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    system_message = SystemMessage(RESPONSE_SYSTEM_PROMPT.strip())
    llm_input: list[BaseMessage] = [system_message]
    llm_input.extend(runtime.context.history_messages)
    current_user_message = state.get("messages", [])[-1]

    last_message = compose_last_human_message_for_node(
        content=cast(str, current_user_message.content),
        relevant_docs=state.get("relevant_docs", None),
    )

    llm_input.extend(last_message)

    llm = with_retry_exception(
        get_language_model(
            model="openai/gpt-oss-120b",
            temperature=1.0,
        )
    )

    response = llm.invoke(llm_input)

    return {"messages": response}
