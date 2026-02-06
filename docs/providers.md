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
The `src/providers/base.py` defines the `LLMProvider` interface which all implementations must follow (Generate, Stream, Tool Call).
