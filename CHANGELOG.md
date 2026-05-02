# Changelog

## v0.1.0 — MCP Server Integration (2026-05-03)

### New Features

#### MCP Server Integration
- New `module/mcp/` package with 11 MCP tools
  - `alas_get_instances`, `alas_start_instance`, `alas_run_task`
  - `alas_get_screenshot`, `alas_get_config`, `alas_set_config`
  - `alas_get_status`, `alas_get_logs`, `alas_stop_instance`
  - `alas_reload_config`, `alas_update_check`
- **stdio transport** — local AI assistants (WorkBuddy, Claude Desktop, Cursor)
- **SSE transport** — remote/web access via `http://<ip>:22267/mcp/sse`
- Mounted on existing FastAPI server in `module/webui/fastapi.py`

#### REST API (Phase 1)
- New `module/api/` package with 11 API endpoints
- Configuration read/write, status query, logs, screenshots, start/stop
- CORS enabled for cross-origin access (mobile web, etc.)
- Port: 22267 (shared with original WebUI)

#### MCP Settings Page (WebUI)
- New "MCP" sidebar button in WebUI
- Shows MCP server status, available tools, and configuration guides
- Supports WorkBuddy, Claude Desktop, and SSE remote access instructions

### Architecture

No additional wrapper needed — Electron (`toolkit/webapp/alas.exe`) natively provides:
- System tray (Tray + Menu API)
- Python process management (python-shell)
- Single instance detection
- Auto-update

Startup flow:
```
Alas.bat → deploy.installer → toolkit/webapp/alas.exe (Electron)
  → Electron spawns gui.py (Python backend)
  → Backend starts FastAPI on port 22267
  → MCP Server auto-available at /mcp/sse
```

### Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| mcp | 1.12.1 | MCP SDK |
| fastapi | 0.136.1 | Web API + SSE |
| uvicorn | 0.46.0 | ASGI server |
