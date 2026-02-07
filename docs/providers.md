# LLM Providers

Light Agent uses `litellm` to abstract interaction with different LLM providers.

## Supported Providers

### 1. Ollama (Local)
Primary choice for local execution.
- **Model**: Defaulting to `llama3` or `mistral`.
- **Config**: `OLLAMA_BASE_URL` (default: http://localhost:11434).

### 2. Google Gemini
Used for high-reasoning tasks or when local resources are limited.
- **Config**: `GOOGLE_API_KEY`.

### 3. LLMStudy
Integration for LLMStudy specific endpoints.
- **Config**: Compatible with OpenAI-style endpoint configuration.

## Provider Abstraction
## Specialized Model Roles

Light Agent supports using different models for different tasks to balance speed and reasoning capability.

### Configuration

You can define specialized models in your `.env` file:

- **`DEFAULT_MODEL`**: The fallback model used if specialized roles are not defined.
- **`FAST_MODEL`**: Used for routine, low-latency tasks like interaction summarization.
- **`REASONING_MODEL`**: Used for the main agent loop, planning, and complex tool execution.

Example `.env` setup:
```env
DEFAULT_MODEL="ollama/llama3"
FAST_MODEL="ollama/phi3"      # Lightweight/Fast
REASONING_MODEL="ollama/llama3:70b" # Powerful/Reasoning
```

### Subagents
Subagents default to using the `REASONING_MODEL`. However, when spawning a subagent via the `spawn` tool, a specific model can be optionally provided to override this default.
