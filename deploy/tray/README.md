# AlasTray

**All-in-one launcher + system tray for AzurLaneAutoScript.**

## What is this?

`AlasTray.exe` is the **single entry point** for ALAS.

1. Double-click → runs `deploy.installer` (git update, pip install)
2. Installer success → starts Electron WebUI automatically
3. System tray icon appears (常驻) with right-click menu

## Files

| File | Purpose |
|------|---------|
| `tray.py` | Tray application source (includes launcher logic) |
| `build.py` | PyInstaller build script |
| `../../AlasTray.exe` | Built artifact (place in ALAS root) |

## Build

```batch
cd E:\AzurLaneAutoScript
.venv\Scripts\python.exe deploy\tray\build.py
```

Output: `AlasTray.exe` (in ALAS root directory)

## Usage

```batch
:: Method 1: Double-click AlasTray.exe
:: Method 2: Run Alas.bat (launches AlasTray.exe)
```

## Tray Menu

- **Open WebUI** — bring WebUI to front (or restart if not running)
- **Restart WebUI** — stop and restart Electron
- **Open Config Folder** — open `config/` in Explorer
- **Exit** — stop WebUI and close tray

## Architecture

```
User double-clicks AlasTray.exe
    ↓
AlasTray runs deploy.installer
    ↓
On success: starts toolkit/webapp/alas.exe (Electron)
    ↓
Shows system tray icon
    ↓
Right-click menu for control
```

No separate launcher needed — AlasTray does it all.
