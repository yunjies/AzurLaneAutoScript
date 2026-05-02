# ALAS MCP Server

Model Context Protocol (MCP) integration for AzurLaneAutoScript.

Lets AI agents (Claude Desktop, Cursor, etc.) inspect and control ALAS instances via natural language.

## Requirements

```bash
pip install mcp
```

Already installed in ALAS venv.

## Tools (11 total)

| Tool | Purpose |
|------|---------|
| `alas_get_instances` | List all instances with status |
| `alas_get_instance` | Get single instance details |
| `alas_start_instance` | Start scheduler loop |
| `alas_stop_instance` | Stop scheduler loop |
| `alas_run_task` | Run a task once (e.g. `Main`, `Commission`) |
| `alas_reload_config` | Reload config from disk |
| `alas_get_config` | Read full JSON config |
| `alas_update_config` | Merge partial JSON into config |
| `alas_get_config_args` | Get config schema (args.json) |
| `alas_get_log` | Read recent log lines |
| `alas_get_screenshot` | Capture device screenshot (base64 PNG) |

## Usage

### stdio (Claude Desktop / Cursor)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "alas": {
      "command": "E:\\AzurLaneAutoScript\\.venv\\Scripts\\python.exe",
      "args": ["-m", "module.mcp.stdio"],
      "cwd": "E:\\AzurLaneAutoScript"
    }
  }
}
```

### SSE (web / remote)

ALAS WebUI must be running. Then open:

```
http://127.0.0.1:22267/mcp/sse
```

The MCP client connects to this endpoint for server-sent events.
Messages are posted to `/mcp/messages/`.

## Architecture

```
module/mcp/
├── tools.py      # 11 sync tool wrappers (reuses module/api/ logic)
├── server.py     # mcp.server.Server with tool registration
├── stdio.py      # stdio transport entry point
└── README.md     # this file
```

The MCP layer is thin — it directly calls the same functions used by the REST API (`module/api/utils.py`, `module/api/*_api.py`). No duplicated business logic.
