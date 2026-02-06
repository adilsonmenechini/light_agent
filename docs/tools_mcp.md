# Tools and MCP Configuration

Light Agent supports internal skills, built-in tools, and external MCP (Model Context Protocol) servers. All of these can be toggled and configured via the `.env` file.

## Internal Skills (Markdown)
Stored in `workspace/skills/`. The agent discovers these automatically but can be restricted via `ENABLED_SKILLS` in `.env`.

## Built-in Tools
Standard tools provided by the core engine:
- `shell_command`: Execute authorized shell commands.
- `fetch_content`: Basic HTTP GET wrapper.
- `memory_search`: Semantic or keyword search in `workspace/memory/`.

## MCP Servers (External)
You can connect to external MCP servers by defining them in `workspace/servers_config.json`.

### Configuration Pattern (workspace/servers_config.json)
```json
{
  "mcpServers": {
    "googledrive": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-googledrive"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

```env
# Enabled Tools/Skills
ENABLED_TOOLS="shell_command,fetch_content"
AUTO_APPROVE_SHELL=false
```

## How it Works
1. On startup, the `ToolRegistry` parses `ENABLED_TOOLS` and any `MCP_SERVER_*` variables.
2. It initializes MCP clients for each server.
3. It bundles all available tools into a JSON schema for the LLM.
4. When the LLM makes a call, the `Dispatcher` routes it to either a local function, a Markdown skill, or an MCP server.
