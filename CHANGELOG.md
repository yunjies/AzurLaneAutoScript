# Changelog

## v0.1.0 — AlasTray + MCP Server (2026-05-02)

### New Features

#### AlasTray — Windows System Tray Wrapper
- New `deploy/tray/tray.py` — system tray application using **pystray**
- Auto-starts Electron WebUI when tray launches
- Right-click menu: Open WebUI / Restart WebUI / Open Config Folder / Exit
- Graceful WebUI process cleanup on exit
- Backward compatible: falls back to original `webapp/alas.exe` if AlasTray missing

#### PyInstaller-based Launcher
- New `deploy/launcher/launcher.py` — Python-based launcher replacing legacy **Bat-To-Exe Converter**
- New `deploy/launcher/build.py` — PyInstaller build script for `Alas.exe`
- Smaller, more maintainable launcher (7.9MB vs legacy wrapper)

#### MCP Server Integration (Phase 2)
- New `module/mcp/` package with 11 MCP tools
  - `alas_get_instances`, `alas_start_instance`, `alas_run_task`
  - `alas_get_screenshot`, `alas_get_config`, `alas_set_config`
  - `alas_get_status`, `alas_get_logs`, `alas_stop_instance`
  - `alas_reload_config`, `alas_update_check`
- **stdio transport** — local AI assistants (WorkBuddy, Claude Desktop, Cursor)
- **SSE transport** — remote/web access via `http://<ip>:22267/mcp/sse`
- Mounted on existing FastAPI server in `module/webui/fastapi.py`

### Changes

- `deploy/launcher/Alas.bat` — now prefers `AlasTray.exe` if available, otherwise falls back to `webapp/alas.exe`
- Removed legacy launcher code (`deploy/launcher/alas_launcher.py`, `mcp_server.py`)
- Restored Docker files to upstream versions

### Build Artifacts

| File | Size | Description |
|------|------|-------------|
| `Alas.exe` | 7.9 MB | New PyInstaller launcher |
| `toolkit/AlasTray/AlasTray.exe` | 27 MB | System tray manager |

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

:: Build AlasTray.exe
.venv\Scripts\python.exe deploy\tray\build.py

:: Build Alas.exe (new launcher)
.venv\Scripts\python.exe deploy\launcher\build.py
```
