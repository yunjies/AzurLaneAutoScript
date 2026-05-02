# Alas — Launcher + System Tray

**All-in-one launcher + system tray for AzurLaneAutoScript.**

## What is this?

`Alas.exe` is the **single entry point** for ALAS.

1. Double-click → runs `deploy.installer` (git update, pip install)
2. Installer success → starts Electron WebUI automatically
3. System tray icon appears (常驻) with right-click menu

## Files

| File | Purpose |
|------|---------|
| `tray.py` | Main application source (installer + WebUI + tray) |
| `build.py` | PyInstaller build script |
| `../../Alas.exe` | Built artifact (in ALAS root) |

## Build

```batch
cd E:\AzurLaneAutoScript
.venv\Scripts\python.exe deploy\tray\build.py
```

Output: `Alas.exe` (in ALAS root directory)

## Usage

```batch
:: Method 1: Double-click Alas.exe
:: Method 2: Run Alas.bat (launches Alas.exe)
```

## Tray Menu

- **Open WebUI** — bring WebUI to front (or restart if not running)
- **Restart WebUI** — stop and restart Electron
- **Open Config Folder** — open `config/` in Explorer
- **Exit** — stop WebUI and close tray

## Important Notes

- Built with `--windowed` flag (no console window). **Never use `input()` or
  `print()` expecting user to see it** — use `_show_error()` (MessageBox) for
  critical errors and `_log()` (file log) for diagnostics.

## Architecture

```
User double-clicks Alas.exe
    ↓
Alas runs deploy.installer
    ↓
On success: starts toolkit/webapp/alas.exe (Electron)
    ↓
Shows system tray icon
    ↓
Right-click menu for control
```

No separate launcher needed — Alas.exe does it all.
