import os
from typing import Literal, TypedDict, Unpack

from groq import BadRequestError
from langchain_core.runnables import Runnable
from langchain_groq import ChatGroq

GROQ_API_KEY = os.getenv("GROQ_API_KEY", None)

if GROQ_API_KEY is None:
    raise ValueError("'GROQ_API_KEY' is not found")

_LLM_MODEL_RAW = os.getenv("LLM_MODEL", "openai/gpt-oss-20b").strip()
LLM_MODEL = _LLM_MODEL_RAW or "openai/gpt-oss-20b"


class ModelKwargs(TypedDict, total=False):
    model: str
    temperature: int | float
    max_tokens: int | None
    reasoning_format: Literal["parsed", "raw", "hidden"]
    reasoning_effort: Literal["low", "medium", "high"]


def with_retry_exception(runnable: Runnable) -> Runnable:
    return runnable.with_retry(retry_if_exception_type=(BadRequestError,))


def get_language_model(**kwargs: Unpack[ModelKwargs]):
    model = kwargs.get("model", LLM_MODEL)
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

    return llm
