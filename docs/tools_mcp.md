# Tools and MCP Configuration

Light Agent supports internal skills, built-in tools, and external MCP (Model Context Protocol) servers. All of these can be toggled and configured via the `.env` file.

## Internal Skills (Markdown)
Stored in `workspace/skills/`. The agent discovers these automatically but can be restricted via `ENABLED_SKILLS` in `.env`.

## Built-in Tools
Standard tools provided by the core engine:

### File Operations
- `read_file`: Read file contents (restricted to workspace if enabled)
- `write_file`: Write content to files (restricted to workspace)
- `list_dir`: List directory contents (restricted to workspace)
- `edit_file`: Edit files by replacing text

### Shell Execution
- `exec`: Execute shell commands with security restrictions:
  - Only 60+ pre-approved commands allowed
  - Shell metacharacters blocked (`;|&$<>`{}[]\\*?\n\r)
  - Destructive patterns blocked (`rm -rf`, fork bombs)
  - Uses subprocess isolation instead of shell=True

### Web Tools
- `web_search`: Search via DuckDuckGo
- `web_fetch`: Fetch and parse web content with SSRF protection:
  - Private IP ranges blocked
  - Cloud metadata endpoints blocked
  - DNS resolution validation

### Memory Tools
- `long_memory.search`: Semantic search in past interactions (SQLite + BM25)
- `long_memory.store`: Store new memories
- `long_memory.get_recent`: Retrieve recent context

### Subagent Tools
- `spawn`: Launch a single subagent for a background task
- `parallel_spawn`: Launch multiple subagents concurrently
- `wait_subagents`: Coordinate and wait for results from background subagents

## Security Configuration

All security features are enabled by default:

```env
# Security Settings
RESTRICT_TO_WORKSPACE=true    # Confine file operations to workspace
```

### Allowed Shell Commands

The following command categories are permitted:

| Category | Commands |
|----------|----------|
| Version Control | git, gh, hg |
| File Operations | ls, cat, head, tail, cp, mv, rm, mkdir, touch, chmod, chown |
| Text Processing | grep, sed, awk, jq, yq |
| System Info | pwd, whoami, hostname, uname, date, ps, kill |
| Compression | tar, gzip, zip, unzip |
| Networking | curl, wget, ping, dig, nslookup |
| Containers | docker, kubectl, helm |
| Dev Tools | python, pip, npm, node, uv |
| Cloud CLI | aws, gcloud, az |

### SSRF Protection

Web tools block access to:

| Type | Examples |
|------|----------|
| Private IPs | 10.x.x.x, 172.16.x.x, 192.168.x.x |
| Loopback | 127.0.0.1, ::1 |
| Link-local | 169.254.x.x |
| Cloud Metadata | 169.254.169.254, metadata.google.internal |

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
