# AlasTray

System tray wrapper for AzurLaneAutoScript.

## What is this?

AlasTray provides a **常驻 system tray icon** for ALAS.

- **Auto-starts WebUI** when ALAS launches
- **Tray menu**: Open WebUI / Restart WebUI / Open Config Folder / Exit
- **Process management**: gracefully stops WebUI on exit

## Files

| File | Purpose |
|------|---------|
| `tray.py` | Tray application source |
| `build.py` | PyInstaller build script for `AlasTray.exe` |
| `../../toolkit/AlasTray/AlasTray.exe` | Built artifact |

## Build

```batch
cd E:\AzurLaneAutoScript
.venv\Scripts\python.exe deploy\tray\build.py
```

Output: `toolkit/AlasTray/AlasTray.exe`

## How it integrates

1. `Alas.bat` (or `Alas.exe`) runs `deploy.installer`
2. After installer succeeds, it checks for `toolkit\AlasTray\AlasTray.exe`
3. If found → launches AlasTray (which auto-starts WebUI internally)
4. If not found → falls back to `toolkit\webapp\alas.exe` (original behavior)

## Rebuild launcher (Alas.exe)

If you want a modern `Alas.exe` (PyInstaller-based, no Bat-To-Exe needed):

```batch
cd E:\AzurLaneAutoScript
.venv\Scripts\python.exe deploy\launcher\build.py
```

This replaces the root `Alas.exe` with a Python-based launcher that supports AlasTray natively.
