from typing import Any, AsyncGenerator, Dict, List, Optional, cast

import litellm
from loguru import logger

from lightagent.providers.base import LLMProvider, LLMResponse


class LiteLLMProvider(LLMProvider):
    """Provider using LiteLLM for unified API access."""

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def is_reasoning_model(self, model: Optional[str] = None) -> bool:
        """Check if model is a reasoning model (e.g., o1, o3, DeepSeek R1)."""
        model_name = model or self.model
        reasoning_patterns = ["o1", "o2", "o3", "o4", "deepseek", "r1", "reasoning"]
        return any(pattern in model_name.lower() for pattern in reasoning_patterns)

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

        # Extract reasoning_content for models that support it (OpenAI o1/o3, DeepSeek R1, etc.)
        # Try multiple field names that LiteLLM might use
        reasoning_content = (
            getattr(choice.message, "reasoning_content", None)
            or getattr(choice.message, "reasoning", None)
            or getattr(choice.message, "thinking", None)
        )

        # Debug log for troubleshooting
        if reasoning_content:
            logger.debug(f"Reasoning content extracted: {len(reasoning_content)} chars")

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            raw=response,
            reasoning_content=reasoning_content,
        )

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response for lower perceived latency."""
        model_to_use = model or self.model

        # Reasoning models often don't support streaming
        if self.is_reasoning_model(model_to_use):
            response = await self.generate(messages, tools, model)
            if response.content:
                yield response.content
            return

        stream = await litellm.acompletion(
            model=model_to_use,
            messages=messages,
            tools=tools,
            api_key=self.api_key,
            base_url=self.base_url,
            stream=True,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def get_default_model(self) -> str:
        return self.model
