# Changelog

## v0.1.0 — Alas + MCP Server (2026-05-02)

### New Features

#### Alas — All-in-One Launcher + System Tray
- Single `Alas.exe` replaces both legacy launcher and separate tray app
- Double-click → runs `deploy.installer` → starts WebUI → shows tray icon
- Right-click menu: Open WebUI / Restart WebUI / Open Config Folder / Exit
- Graceful WebUI process cleanup on exit
- File-based logging (`log/alas_tray.log`) — no console dependency
- Windows MessageBox for critical errors (works in `--windowed` mode)
- Source: `deploy/tray/tray.py`, Build: `deploy/tray/build.py`

#### MCP Server Integration (Phase 2)
- New `module/mcp/` package with 11 MCP tools
  - `alas_get_instances`, `alas_start_instance`, `alas_run_task`
  - `alas_get_screenshot`, `alas_get_config`, `alas_set_config`
  - `alas_get_status`, `alas_get_logs`, `alas_stop_instance`
  - `alas_reload_config`, `alas_update_check`
- **stdio transport** — local AI assistants (WorkBuddy, Claude Desktop, Cursor)
- **SSE transport** — remote/web access via `http://<ip>:22267/mcp/sse`
- Mounted on existing FastAPI server in `module/webui/fastapi.py`

#### MCP Settings Page (WebUI)
- New "MCP" sidebar button in WebUI
- Shows MCP server status, available tools, and configuration guides
- Supports WorkBuddy, Claude Desktop, and SSE remote access instructions

### Changes

- `deploy/launcher/Alas.bat` — simplified to launch `Alas.exe` directly
- Removed legacy launcher code (`alas_launcher.py`, `mcp_server.py`)
- Removed separate launcher/build scripts
- Restored Docker files to upstream versions

### Build Artifacts

| File | Size | Description |
|------|------|-------------|
| `Alas.exe` | ~27 MB | Single entry point: installer + WebUI + tray |

### Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| mcp | 1.12.1 | MCP SDK |
| pystray | 0.19.5 | System tray icon |
| pyinstaller | 6.20.0 | EXE packaging |
| fastapi | 0.136.1 | Web API + SSE |
| uvicorn | 0.46.0 | ASGI server |

---

## How to Build

```batch
cd E:\AzurLaneAutoScript

:: Build Alas.exe (single entry point)
.venv\Scripts\python.exe deploy\tray\build.py
```

Output: `Alas.exe` in ALAS root directory.
