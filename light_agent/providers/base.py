from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    raw: Any = None
    reasoning_content: Optional[str] = None

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls and len(self.tool_calls) > 0)

    @property
    def has_reasoning(self) -> bool:
        return bool(self.reasoning_content and len(self.reasoning_content) > 0)


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        pass
