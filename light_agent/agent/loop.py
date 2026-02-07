import json
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger

from light_agent.agent.memory import MemoryStore
from light_agent.agent.short_memory import ShortTermMemory
from light_agent.agent.tools import ToolRegistry
from light_agent.agent.tools.memory_tool import LongMemoryTool
from light_agent.config.settings import settings
from light_agent.core import emit_llm_call, emit_tool_end, emit_tool_start
from light_agent.providers.base import LLMProvider


def _extract_insight_from_tool_result(
    tool_name: str, tool_args: Dict[str, Any], tool_result: str
) -> Optional[str]:
    """
    Extract a meaningful insight from a tool result.
    Returns None if the result is not worth saving as an observation.
    """
    result = tool_result.strip()

    # Skip empty or error results
    if not result or result.lower().startswith(("error:", "failed", "exception")):
        return None

    # Skip very short results that don't contain meaningful information
    if len(result) < 20:
        return None

    # Truncate very long results
    if len(result) > 2000:
        result = result[:2000] + "... [truncated]"

    # Generate insight based on tool type
    insights = {
        "read_file": f"Lido arquivo: descobriu que {result[:300]}..."
        if len(result) > 300
        else f"Lido arquivo: {result}",
        "write_file": f"Criou/editou arquivo com conteúdo: {result[:300]}..."
        if len(result) > 300
        else f"Criou/editou arquivo: {result}",
        "list_dir": f"Listou diretório: encontrou {result.count(chr(10)) + 1} itens",
        "exec": f"Executou comando que retornou: {result[:300]}..."
        if len(result) > 300
        else f"Executou comando: {result}",
        "grep": f"Busca encontrou {result.count(chr(10)) + 1} resultados",
        "glob": f"Encontrou {result.count(chr(10)) + 1} arquivos correspondendo ao padrão",
        "edit": f"Editou arquivo: {result}",
        "web_search": f"Pesquisa web retornou {result.count(chr(10)) + 1} resultados",
        "web_fetch": f"Conteúdo web extraído: {result[:300]}..."
        if len(result) > 300
        else f"Conteúdo web: {result}",
    }

    return insights.get(tool_name, f"Tool {tool_name} executou: {result[:300]}...")


class AgentLoop:
    def __init__(
        self,
        provider: LLMProvider,
        memory: MemoryStore,
        tools: ToolRegistry,
        long_memory: Optional[LongMemoryTool] = None,
        short_memory: Optional[ShortTermMemory] = None,
    ):
        self.provider = provider
        self.memory = memory
        self.tools = tools
        self.long_memory = long_memory
        self.short_memory = short_memory or ShortTermMemory()
        self.messages: List[Dict[str, str]] = []
        self.conversation_id = self._generate_id()

    def _generate_id(self) -> str:
        return str(uuid.uuid4())[:8]

    def clear_messages(self):
        """Clear conversation history and start a new conversation ID."""
        self.messages = []
        self.conversation_id = self._generate_id()
        if self.short_memory:
            self.short_memory.clear_all()

    async def run(self, user_input: str):
        # Initial context
        if not self.messages:
            self.messages.append({"role": "system", "content": self._get_system_prompt()})

        self.messages.append({"role": "user", "content": user_input})

        # Sync with short-term memory
        if self.short_memory:
            self.short_memory.add_message("user", user_input)

        final_answer = ""
        max_iterations = 10
        for i in range(max_iterations):
            logger.debug(f"Iteration {i + 1}")

            tool_schemas = await self.tools.get_all_tool_schemas()
            reasoning_model = settings.REASONING_MODEL or settings.DEFAULT_MODEL

            emit_llm_call(reasoning_model, len(self.messages))

            response = await self.provider.generate(
                self.messages,
                tools=tool_schemas if tool_schemas else None,
                model=reasoning_model,
            )

            if response.content:
                logger.info(f"Agent: {response.content}")
                self.messages.append({"role": "assistant", "content": response.content})
                final_answer = response.content

                # Sync assistant message to short-term memory
                if self.short_memory:
                    self.short_memory.add_message("assistant", response.content)

            if not response.tool_calls:
                break

            # Handle Tool Calls
            for tool_call in response.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                emit_tool_start(name, args)
                result = await self.tools.call_tool(name, args)
                emit_tool_end(name, result)

                self.messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "name": name, "content": result}
                )

                # Auto-capture tool observations if long_memory is available
                if self.long_memory:
                    insight = _extract_insight_from_tool_result(name, args, result)
                    if insight:
                        try:
                            await self.long_memory.store_observation(
                                conversation_id=self.conversation_id,
                                tool_name=name,
                                tool_input=args,
                                tool_output=result,
                                insight=insight,
                            )
                        except Exception as e:
                            logger.warning(f"Failed to store tool observation: {e}")

        # Summarize and log to memory
        summary = await self._summarize(user_input, final_answer)

        entry = {
            "conversation_id": self.conversation_id,
            "question": user_input,
            "answer": final_answer,
            "summary": summary,
        }

        # Log standalone memory entry if available
        if self.long_memory:
            await self.long_memory.store(entry)

        return final_answer or "Error: No response generated"

    async def _summarize(self, question: str, answer: str) -> str:
        """Generate a short summary of the Q&A."""
        try:
            prompt = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes conversations concisely in Portuguese.",
                },
                {
                    "role": "user",
                    "content": f"Resuma a seguinte interação entre um usuário e um assistente SRE em uma frase curta:\nPergunta: {question}\nResposta: {answer}",
                },
            ]
            fast_model = settings.FAST_MODEL or settings.DEFAULT_MODEL
            response = await self.provider.generate(prompt, model=fast_model)
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

        # Get short-term memory context (current session)
        session_context = ""
        observations_context = ""
        if self.short_memory:
            session_context = self.short_memory.get_message_window()
            observations_context = self.short_memory.get_observations_summary()

        skills_summary = "No detailed skills loaded."
        if self.tools.skills_loader:
            skills_summary = self.tools.skills_loader.get_skills_summary()

        return f"""You are a lightweight SRE agent.

# Long-term Knowledge (Fixed Facts)
{memory_context or "No fixed facts available."}

{recent_history}

{session_context}

{observations_context}

# Available Skills
{skills_summary}

# Instructions
1. Use the available tools to fulfill user requests.
2. For GitHub public repositories WITHOUT authentication: use 'github_public' tool with action='repo_info', 'repo_contents', 'repo_tree', or 'file_content'.
3. For GitHub with authentication (PRs, issues, etc.): use 'github' tool (requires 'gh auth login').
4. If you need to search the web, use 'web_search'.
4. Search historical conversations using 'long_memory.search' if you need to recall information from past sessions or technical context provided previously. Prefer this over assuming the user will repeat themselves.
5. Do not refuse tasks that can be accomplished with your tools and skills.
6. Be concise and efficient.
7. A sua resposta final deve ser em Português se o usuário perguntar em Português."""
