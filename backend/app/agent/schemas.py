from pydantic import BaseModel, Field


class RefinedRetrievalQuery(BaseModel):
    """
    Represents a standalone search query derived from the conversation, used for
    semantic document retrieval (embedding similarity search).
    """

    refined_query: str = Field(
        ...,
        description=(
            "A short, non-empty string suitable for embedding-based similarity search. "
            "Resolve pronouns, implicit references, and missing entity names using the "
            "conversation; do not answer the user's question or invent facts not implied "
            "by the dialogue."
        ),
    )
