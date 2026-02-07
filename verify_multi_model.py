import asyncio
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from light_agent.agent.loop import AgentLoop
from light_agent.config.settings import settings
from light_agent.providers.base import LLMProvider, LLMResponse

class MockProvider(LLMProvider):
    def __init__(self):
        self.generate = AsyncMock()
    
    async def generate(self, messages, tools=None, model=None) -> LLMResponse:
        return await self.generate(messages, tools=tools, model=model)
        
    def get_default_model(self):
        return "default-model"

class TestMultiModel(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.provider = MockProvider()
        self.memory = MagicMock()
        self.tools = MagicMock()
        self.tools.get_all_tool_schemas = AsyncMock(return_value=[])
        self.loop = AgentLoop(self.provider, self.memory, self.tools)

    @patch("light_agent.agent.loop.settings")
    async def test_agent_loop_model_selection(self, mock_settings):
        # Setup specific models
        mock_settings.REASONING_MODEL = "gpt-4-reasoning"
        mock_settings.FAST_MODEL = "gpt-3.5-fast"
        
        # Configure response
        self.provider.generate.return_value = LLMResponse(content="Final answer", tool_calls=[])
        
        # Run loop
        await self.loop.run("Hello")
        
        # Check if the main loop used reasoning model
        # The first call in run() is the main iteration
        # The second call is _summarize
        
        calls = self.provider.generate.call_args_list
        print(f"\nCalls to provider.generate: {len(calls)}")
        for idx, call in enumerate(calls):
            model_used = call.kwargs.get('model')
            print(f"Call {idx+1} model: {model_used}")
            
        self.assertEqual(calls[0].kwargs.get('model'), "gpt-4-reasoning")
        self.assertEqual(calls[1].kwargs.get('model'), "gpt-3.5-fast")

if __name__ == "__main__":
    unittest.main()
