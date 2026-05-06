import sys

from langchain_core.messages import BaseMessage, HumanMessage


REFINE_SYSTEM_PROMPT = """
You rewrite user turns into a short standalone search query for semantic
document retrieval. Use the full conversation to resolve pronouns,
implicit references, and missing entity names. Do not answer the user's
question and do not add facts that are not implied by the dialogue.
Populate the structured output field refined_query with a non-empty string
suitable for embedding search.
"""

RESPONSE_SYSTEM_PROMPT = """
You are a helpful assistant. Use the conversation history when relevant.
The final user message may contain labeled sections: retrieved context
(for grounding) and the current request. Answer the current request,
using retrieved context when it applies.
Format every reply as Markdown (e.g. **bold**, lists, `inline code`,
## headings when helpful); plain paragraphs are fine.
Do not wrap the entire answer in a fenced code block unless you are
showing actual code.
"""


def compose_last_human_message_for_node(
    content: str,
    relevant_docs: list | None = None,
) -> list[BaseMessage]:
    node_name = sys._getframe(1).f_code.co_name
    text = content.strip()

    if node_name == "refine_query":
        return [
            HumanMessage(
                content=(
                    "Latest user message:\n"
                    f"{text}\n\n"
                    "Produce the structured output with a non-empty refined_query."
                )
            )
        ]

    if node_name == "response":
        ctx = (
            "No relevant documents found"
            if relevant_docs is None
            else str(relevant_docs)
        )

        return [
            HumanMessage(
                content=(
                    "The following is a single user turn with two labeled parts.\n\n"
                    "--- Retrieved context ---\n"
                    f"{ctx}\n\n"
                    "--- Current request ---\n"
                    f"{text}"
                )
            )
        ]

    raise ValueError(
        f"Unknown function name for compose_last_human_message_for_node: {sys._getframe(1).f_code.co_name!r}"
    )
