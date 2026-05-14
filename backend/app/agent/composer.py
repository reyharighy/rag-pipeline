import sys

from langchain_core.messages import BaseMessage, HumanMessage

from app.services.prompt_templates import (
    RESPONSE_USER,
    get_refinement_user_message_template,
    get_template_body,
    render_mustache_template,
)


def compose_last_human_message_for_node(
    content: str,
    relevant_docs: list | None = None,
) -> list[BaseMessage]:
    node_name = sys._getframe(1).f_code.co_name
    text = content.strip()

    if node_name == "refine_query":
        tpl = get_refinement_user_message_template()
        rendered = render_mustache_template(tpl, {"question": text})

        return [HumanMessage(content=rendered)]

    if node_name == "response":
        ctx = (
            "No relevant documents found"
            if relevant_docs is None
            else str(relevant_docs)
        )

        tpl = get_template_body(RESPONSE_USER)

        rendered = render_mustache_template(
            tpl,
            {"context": ctx, "question": text},
        )

        return [HumanMessage(content=rendered)]

    raise ValueError(
        f"Unknown function name for compose_last_human_message_for_node: {sys._getframe(1).f_code.co_name!r}"
    )
