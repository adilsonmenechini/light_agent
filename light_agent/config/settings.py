from pathlib import Path
from typing import Dict, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Workspace
    WORKSPACE_DIR: Path = Path("./workspace")

    # LLM Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GOOGLE_API_KEY: Optional[str] = None
    LLMSTUDY_API_KEY: Optional[str] = None
    LLMSTUDY_BASE_URL: Optional[str] = None

    DEFAULT_MODEL: str = "ollama/llama3"
    FAST_MODEL: Optional[str] = None
    REASONING_MODEL: Optional[str] = None

    # Tool Configuration
    ENABLED_TOOLS: str = "shell_command,fetch_content"
    AUTO_APPROVE_SHELL: bool = False

    # MCP Configuration
    # Pattern: MCP_SERVER_<NAME>="command"
    # Example: MCP_SERVER_FETCH="npx @modelcontextprotocol/server-fetch"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    @property
    def mcp_servers(self) -> Dict[str, str]:
        """Extrae servidores MCP definidos en workspace/servers_config.json."""
        config_path = self.WORKSPACE_DIR / "servers_config.json"
        if not config_path.exists():
            return {}

        try:
            import json

            data = json.loads(config_path.read_text(encoding="utf-8"))
            # Expecting format: {"mcpServers": {"name": {"command": "...", "args": [...]}}}
            # Or simpler: {"servers": {"name": "command"}}
            # Let's support a simple flat dict for now: {"name": "command"}
            return data.get("mcpServers", data)
        except Exception as e:
            from loguru import logger

            logger.error(f"Error reading MCP config from {config_path}: {e}")
            return {}


settings = Settings()
