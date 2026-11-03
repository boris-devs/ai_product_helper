from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: Literal["system", "user", "assistant"]
    content: str


class LLMClient(Protocol):
    @property
    def model_name(self) -> str: ...

    async def complete(self, messages: list[ChatMessage]) -> str: ...
