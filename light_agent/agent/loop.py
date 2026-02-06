import json
import uuid
from typing import Dict, List, Optional

from loguru import logger

from light_agent.agent.memory import MemoryStore
from light_agent.agent.tools import ToolRegistry
from light_agent.agent.tools.memory_tool import LongMemoryTool
from light_agent.providers.base import LLMProvider


class AgentLoop:
    def __init__(self, provider: LLMProvider, memory: MemoryStore, tools: ToolRegistry, long_memory: Optional[LongMemoryTool] = None):
        self.provider = provider
        self.memory = memory
        self.tools = tools
        self.long_memory = long_memory
        self.messages: List[Dict[str, str]] = []
        self.conversation_id = self._generate_id()

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def clear_messages(self):
        """Clear conversation history and start a new conversation ID."""
        self.messages = []
        self.conversation_id = self._generate_id()

    async def run(self, user_input: str):
        # Initial context
        if not self.messages:
            self.messages.append({"role": "system", "content": self._get_system_prompt()})

        self.messages.append({"role": "user", "content": user_input})

        final_answer = ""
        max_iterations = 10
        for i in range(max_iterations):
            logger.debug(f"Iteration {i + 1}")

            tool_schemas = await self.tools.get_all_tool_schemas()
            response = await self.provider.generate(
                self.messages, tools=tool_schemas if tool_schemas else None
            )

            if response.content:
                logger.info(f"Agent: {response.content}")
                self.messages.append({"role": "assistant", "content": response.content})
                final_answer = response.content

            if not response.tool_calls:
                break

            # Handle Tool Calls
            for tool_call in response.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                result = await self.tools.call_tool(name, args)

                self.messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "name": name, "content": result}
                )

        # Summarize and log to memory
        summary = await self._summarize(user_input, final_answer)
        
        entry = {
            "conversation_id": self.conversation_id,
            "question": user_input,
            "answer": final_answer,
            "summary": summary
        }
        
        # Log standalone memory entry if available
        if self.long_memory:
            await self.long_memory.store(entry)

        return final_answer or "Error: No response generated"

    async def _summarize(self, question: str, answer: str) -> str:
        """Generate a short summary of the Q&A."""
        try:
            prompt = [
                {"role": "system", "content": "You are a helpful assistant that summarizes conversations concisely in Portuguese."},
                {"role": "user", "content": f"Resuma a seguinte interação entre um usuário e um assistente SRE em uma frase curta:\nPergunta: {question}\nResposta: {answer}"}
            ]
            response = await self.provider.generate(prompt)
            return response.content.strip() if response.content else ""
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            return ""

    def _get_system_prompt(self) -> str:
        # Get long-term facts (MEMORY.md)
        memory_context = self.memory.read_long_term()
        
        # Get recent interaction history from SQLite
        recent_history = ""
        if self.long_memory:
            recent_history = self.long_memory.get_recent_context(limit=5)
            
        skills_summary = "No detailed skills loaded."
        if self.tools.skills_loader:
            skills_summary = self.tools.skills_loader.get_skills_summary()

        return f"""You are a lightweight SRE agent. 

# Long-term Knowledge (Fixed Facts)
{memory_context or "No fixed facts available."}

{recent_history}

# Available Skills
{skills_summary}

# Instructions
1. Use the available tools to fulfill user requests.
2. If you need to interact with GitHub, use the 'gh' CLI via the 'exec' tool.
3. If you need to search the web, use 'web_search'.
4. Search historical conversations using 'long_memory.search' if you need to recall information from past sessions or technical context provided previously. Prefer this over assuming the user will repeat themselves.
5. Do not refuse tasks that can be accomplished with your tools and skills.
6. Be concise and efficient.
7. A sua resposta final deve ser em Português se o usuário perguntar em Português."""
