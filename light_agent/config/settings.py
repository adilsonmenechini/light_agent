from pathlib import Path
from typing import Dict, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Base directory (default) and Workspace (optional override)
    BASE_DIR: Path = Path("./light_agent/base")
    WORKSPACE_DIR: Path = Path("./workspace")
    RESTRICT_TO_WORKSPACE: bool = True

    @property
    def effective_base_dir(self) -> Path:
        """Use BASE_DIR if exists, fallback to WORKSPACE_DIR for backwards compatibility."""
        if self.BASE_DIR.exists():
            return self.BASE_DIR
        return self.WORKSPACE_DIR

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
    ENABLE_SUMMARY: bool = True  # Token optimization: disable to skip summary generation

    # MCP Configuration
    # Pattern: MCP_SERVER_<NAME>="command"
    # Example: MCP_SERVER_FETCH="npx @modelcontextprotocol/server-fetch"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="allow")

    @property
    def mcp_servers(self) -> Dict[str, str]:
        """Load MCP servers from BASE_DIR first, fallback to WORKSPACE_DIR."""
        config_path = self.effective_base_dir / "servers_config.json"
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
