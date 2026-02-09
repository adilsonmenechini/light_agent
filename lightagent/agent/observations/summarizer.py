"""AI-powered summarization for tool observations."""

from dataclasses import dataclass
from typing import Optional, Protocol
from datetime import datetime


class LLMProvider(Protocol):
    """Protocol for LLM provider."""

    async def generate(self, messages: list[dict]) -> str: ...


@dataclass
class SummarizationConfig:
    """Configuration for summarization."""

    max_summary_length: int = 150
    include_context: bool = True
    language: str = "pt"  # Default to Portuguese
    style: str = "concise"  # concise, detailed, narrative


# Fallback templates when LLM is not available
_FALLBACK_TEMPLATES = {
    "read_file": lambda r: f"Lido arquivo: {r[:300]}...",
    "write_file": lambda r: f"Criou/editou arquivo com conteúdo: {r[:300]}...",
    "exec": lambda r: f"Executou comando que retornou: {r[:300]}...",
    "grep": lambda r: f"Busca encontrou {r.count(chr(10)) + 1} resultados",
    "list_dir": lambda r: f"Listou diretório: encontrou {r.count(chr(10)) + 1} itens",
    "web_search": lambda r: f"Pesquisa web retornou {r.count(chr(10)) + 1} resultados",
    "web_fetch": lambda r: f"Conteúdo web extraído: {r[:300]}...",
    "edit": lambda r: f"Editou arquivo: {r}",
    "default": lambda r: f"Tool executou: {r[:300]}...",
}


async def generate_summary(
    tool_name: str,
    tool_args: dict,
    tool_result: str,
    llm_provider: Optional[LLMProvider] = None,
    config: Optional[SummarizationConfig] = None,
) -> str:
    """Generate an AI summary of a tool execution.

    Args:
        tool_name: Name of the tool.
        tool_args: Arguments passed to the tool.
        tool_result: Result returned by the tool.
        llm_provider: Optional LLM provider for AI summarization.
        config: Optional configuration for summarization.

    Returns:
        A summary string.
    """
    if config is None:
        config = SummarizationConfig()

    # Check if we should use AI summarization
    if llm_provider is not None and _should_use_ai(tool_name, tool_result):
        return await _ai_summarize(tool_name, tool_args, tool_result, llm_provider, config)

    # Fallback to template-based summary
    return _template_summarize(tool_name, tool_args, tool_result, config)


def _should_use_ai(tool_name: str, tool_result: str) -> bool:
    """Determine if AI summarization should be used."""
    # Use AI for complex results
    complex_tools = {"read_file", "exec", "grep", "web_fetch"}
    if tool_name in complex_tools and len(tool_result) > 500:
        return True
    return False


async def _ai_summarize(
    tool_name: str,
    tool_args: dict,
    tool_result: str,
    llm_provider: LLMProvider,
    config: SummarizationConfig,
) -> str:
    """Generate AI summary using LLM."""
    # Build prompt based on language
    if config.language == "pt":
        prompt = _build_portuguese_prompt(tool_name, tool_args, tool_result, config)
    else:
        prompt = _build_english_prompt(tool_name, tool_args, tool_result, config)

    try:
        messages = [{"role": "user", "content": prompt}]
        summary = await llm_provider.generate(messages)
        return summary.strip()
    except Exception:
        # Fallback to template on error
        return _template_summarize(tool_name, tool_args, tool_result, config)


def _build_portuguese_prompt(
    tool_name: str, tool_args: dict, tool_result: str, config: SummarizationConfig
) -> str:
    """Build Portuguese prompt for summarization."""
    truncated_result = tool_result[:1000] + "..." if len(tool_result) > 1000 else tool_result

    style_instructions = {
        "concise": "Seja extremamente conciso, no máximo 50 palavras.",
        "detailed": "Forneça detalhes relevantes do resultado.",
        "narrative": "Descreva o que aconteceu de forma narrativa.",
    }

    style_text = style_instructions.get(config.style, style_instructions["concise"])
    return f"""Gere um resumo conciso do resultado de uma ferramenta de CLI:

Ferramenta: {tool_name}
Argumentos: {tool_args}
Resultado:
{truncated_result}

{style_text}

Resumo:"""


def _build_english_prompt(
    tool_name: str, tool_args: dict, tool_result: str, config: SummarizationConfig
) -> str:
    """Build English prompt for summarization."""
    truncated_result = tool_result[:1000] + "..." if len(tool_result) > 1000 else tool_result

    style_instructions = {
        "concise": "Be extremely concise, at most 50 words.",
        "detailed": "Provide relevant details from the result.",
        "narrative": "Describe what happened in a narrative form.",
    }

    style_text = style_instructions.get(config.style, style_instructions["concise"])
    return f"""Generate a concise summary of a CLI tool result:

Tool: {tool_name}
Args: {tool_args}
Result:
{truncated_result}

{style_text}

Summary:"""


def _template_summarize(
    tool_name: str, tool_args: dict, tool_result: str, config: SummarizationConfig
) -> str:
    """Generate template-based summary."""
    result = tool_result.strip()

    # Skip empty or error results
    if not result or result.lower().startswith(("error:", "failed", "exception")):
        return f"Erro: {result[:200]}" if config.language == "pt" else f"Error: {result[:200]}"

    # Skip very short results
    if len(result) < 20:
        return result

    # Truncate very long results
    if len(result) > 2000:
        result = result[:2000] + "... [truncated]"

    # Use template if available
    if tool_name in _FALLBACK_TEMPLATES:
        return _FALLBACK_TEMPLATES[tool_name](result)

    return _FALLBACK_TEMPLATES["default"](result)


def get_supported_languages() -> list[str]:
    """Get list of supported languages."""
    return ["pt", "en", "es"]


def get_supported_styles() -> list[str]:
    """Get list of supported summary styles."""
    return ["concise", "detailed", "narrative"]


async def generate_session_summary(
    observations: list[dict], llm_provider: Optional[LLMProvider] = None, language: str = "pt"
) -> str:
    """Generate a summary of an entire session's observations.

    Args:
        observations: List of observation dicts with 'insight', 'category', 'importance'.
        llm_provider: Optional LLM provider.
        language: Language for the summary.

    Returns:
        A session summary string.
    """
    if not observations:
        return (
            "Nenhuma observação nesta sessão."
            if language == "pt"
            else "No observations in this session."
        )

    if llm_provider is not None:
        return await _ai_session_summary(observations, llm_provider, language)

    # Fallback: Group by category
    by_category: dict[str, list] = {}
    for obs in observations:
        cat = obs.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(obs)

    if language == "pt":
        lines = ["Resumo da sessão:"]
        for cat, items in by_category.items():
            lines.append(f"- {cat}: {len(items)} observação(ões)")
        return "\n".join(lines)
    else:
        lines = ["Session summary:"]
        for cat, items in by_category.items():
            lines.append(f"- {cat}: {len(items)} observation(s)")
        return "\n".join(lines)


async def _ai_session_summary(
    observations: list[dict], llm_provider: LLMProvider, language: str
) -> str:
    """Generate AI session summary."""
    # Format observations for the prompt
    obs_texts = []
    for i, obs in enumerate(observations[:20]):  # Limit to 20 observations
        obs_texts.append(
            f"{i + 1}. [{obs.get('category', 'unknown')}] {obs.get('insight', '')[:100]}"
        )

    obs_list = "\n".join(obs_texts)

    if language == "pt":
        prompt = f"""Gere um resumo da sessão atual baseado nas observações:

{obs_list}

Forneça:
1. Principais descobertas
2. Padrões identificados
3. Recomendações

Resumo:
"""
    else:
        prompt = f"""Generate a summary of the current session based on observations:

{obs_list}

Provide:
1. Key findings
2. Patterns identified
3. Recommendations

Summary:
"""

    try:
        messages = [{"role": "user", "content": prompt}]
        return await llm_provider.generate(messages)
    except Exception:
        # Fallback on error
        return (
            "Erro ao gerar resumo da sessão."
            if language == "pt"
            else "Error generating session summary."
        )
