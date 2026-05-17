from typing import Any, cast

from langchain_core.messages import BaseMessage
from langchain_core.messages.system import SystemMessage
from langgraph.runtime import Runtime

from app.services import (
    get_language_model,
    with_retry_exception,
)

from app.services.prompt_templates import (
    REFINE_SYSTEM,
    RESPONSE_SYSTEM,
    get_template_body,
)

from app.config import get_settings
from app.database.tables import VectorDocument

from .composer import compose_last_human_message_for_node
from .runtime import Context
from .schemas import RefinedRetrievalQuery
from .state import State

_embedding_cfg = get_settings().embedding

def refine_query(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    system_message = SystemMessage(get_template_body(REFINE_SYSTEM).strip())
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
    vector_document = VectorDocument(_embedding_cfg.service)
    query_text = cast(str, state.get("refined_query") or "").strip()

    if not query_text:
        query_text = cast(str, state["messages"][-1].content)

    relevant_docs = vector_document.similarity_search(
        query=query_text,
        top_k=8,
    )

    return {"relevant_docs": relevant_docs}


def response(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    system_message = SystemMessage(get_template_body(RESPONSE_SYSTEM).strip())
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
