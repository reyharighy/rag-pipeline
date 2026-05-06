from dataclasses import dataclass, field

from langchain_core.messages import BaseMessage


@dataclass
class Context:
    history_messages: list[BaseMessage] = field(default_factory=list)
