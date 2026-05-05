import os
from typing import Literal, TypedDict, Unpack
from langchain_groq import ChatGroq
from groq import BadRequestError

GROQ_API_KEY = os.getenv("GROQ_API_KEY", None)

if GROQ_API_KEY is None:
    raise ValueError("'GROQ_API_KEY' is not found")

class ModelKwargs(TypedDict, total=False):
    model: Literal["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    temperature: int | float
    max_tokens: int | None
    reasoning_format: Literal["parsed", "raw", "hidden"]
    reasoning_effort: Literal["low", "medium", "high"]


def get_language_model(**kwargs: Unpack[ModelKwargs]):
    model = kwargs.get("model", "openai/gpt-oss-20b")
    temperature = float(kwargs.get("temperature", 0))
    max_tokens = kwargs.get("max_tokens", None)
    reasoning_format = kwargs.get("reasoning_format", "parsed")
    reasoning_effort = kwargs.get("reasoning_effort", "low")

    llm = ChatGroq(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_format=reasoning_format,
        reasoning_effort=reasoning_effort,
        timeout=None,
    )

    llm = llm.with_retry(retry_if_exception_type=(BadRequestError,))

    return llm
