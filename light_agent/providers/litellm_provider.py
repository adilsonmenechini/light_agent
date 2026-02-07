from typing import Any, Dict, List, Optional, cast

import litellm

from light_agent.providers.base import LLMProvider, LLMResponse


class LiteLLMProvider(LLMProvider):
    """Provider using LiteLLM for unified API access."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> LLMResponse:
        model_to_use = model or self.model
        response = await litellm.acompletion(
            model=model_to_use,
            messages=messages,
            tools=tools,
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # Cast to handle LiteLLM's complex type hierarchy
        response_cast = cast(Any, response)
        choice = response_cast.choices[0]
        content = choice.message.content
        tool_calls = getattr(choice.message, "tool_calls", None)

        return LLMResponse(content=content, tool_calls=tool_calls, raw=response)

    def get_default_model(self) -> str:
        return self.model
