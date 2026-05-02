#!/usr/bin/env python3
"""
AlasTray — All-in-one launcher + system tray for AzurLaneAutoScript

Usage:
    Double-click AlasTray.exe (or Alas.bat)

Flow:
    1. Find ALAS root directory
    2. Set up PATH (toolkit, Git, adb, etc.)
    3. Run deploy.installer (git update, pip install, adb install)
    4. Start Electron WebUI
    5. Show system tray icon (常驻)
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from PIL import Image
import pystray

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
TRAY_DIR = Path(__file__).parent.resolve()
DEPLOY_DIR = TRAY_DIR.parent.resolve()
ALAS_ROOT = DEPLOY_DIR.parent.resolve()
ICON_PATH = ALAS_ROOT / "deploy" / "launcher" / "icon.ico"
WEBAPP_PATH = ALAS_ROOT / "toolkit" / "webapp" / "alas.exe"
CONFIG_DIR = ALAS_ROOT / "config"

# ---------------------------------------------------------------------------
# Process state
# ---------------------------------------------------------------------------
_webui_proc = None
_lock = threading.Lock()


def _log(msg: str):
    """Print to stdout with prefix."""
    print(f"[AlasTray] {msg}")


def _setup_env() -> dict:
    """Build PATH env var exactly like Alas.bat does."""
    toolkit = ALAS_ROOT / "toolkit"
    paths = [
        toolkit / "alias",
        toolkit / "command",
        toolkit,
        toolkit / "Scripts",
        toolkit / "Git" / "mingw64" / "bin",
        toolkit / "Lib" / "site-packages" / "adbutils" / "binaries",
    ]
    valid_paths = [str(p) for p in paths if p.exists()]
    env = os.environ.copy()
    env["PATH"] = ";".join(valid_paths) + ";" + env.get("PATH", "")
    return env


def _find_python(env: dict) -> str:
    """Find the Python executable."""
    toolkit_python = ALAS_ROOT / "toolkit" / "python.exe"
    if toolkit_python.exists():
        return str(toolkit_python)
    return "python"


def run_installer() -> bool:
    """Run deploy.installer. Returns True on success."""
    env = _setup_env()
    python_exe = _find_python(env)

    _log("Running installer...")
    result = subprocess.run(
        [python_exe, "-m", "deploy.installer"],
        cwd=str(ALAS_ROOT),
        env=env,
    )
    if result.returncode != 0:
        _log("Installer failed.")
        return False
    _log("Installer completed.")
    return True


def _is_webui_running() -> bool:
    """Check if the WebUI process is still alive."""
    global _webui_proc
    if _webui_proc is None:
        return False
    return _webui_proc.poll() is None


def start_webui():
    """Start the Electron WebUI process."""
    global _webui_proc
    with _lock:
        if _is_webui_running():
            _log("WebUI is already running.")
            return
        if not WEBAPP_PATH.exists():
            _log(f"ERROR: WebUI not found at {WEBAPP_PATH}")
            return
        _log(f"Starting WebUI: {WEBAPP_PATH}")
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        _webui_proc = subprocess.Popen(
            [str(WEBAPP_PATH)],
            cwd=str(WEBAPP_PATH.parent),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **kwargs,
        )
        _log(f"WebUI started (pid={_webui_proc.pid})")


def stop_webui():
    """Stop the Electron WebUI process."""
    global _webui_proc
    with _lock:
        if _webui_proc is None:
            return
        _log(f"Stopping WebUI (pid={_webui_proc.pid})...")
        try:
            if sys.platform == "win32":
                import signal
                os.kill(_webui_proc.pid, signal.CTRL_BREAK_EVENT)
            else:
                _webui_proc.terminate()
            try:
                _webui_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _log("WebUI did not exit gracefully, forcing kill...")
                _webui_proc.kill()
                _webui_proc.wait()
        except ProcessLookupError:
            pass
        except Exception as e:
            _log(f"Error stopping WebUI: {e}")
        finally:
            _webui_proc = None
        _log("WebUI stopped.")


def restart_webui():
    """Restart the WebUI process."""
    _log("Restarting WebUI...")
    stop_webui()
    time.sleep(0.5)
    start_webui()


def open_config_folder():
    """Open the config folder in Explorer."""
    path = str(CONFIG_DIR) if CONFIG_DIR.exists() else str(ALAS_ROOT)
    _log(f"Opening config folder: {path}")
    if sys.platform == "win32":
        os.startfile(path)
    else:
        subprocess.Popen(["xdg-open", path])


# ---------------------------------------------------------------------------
# Tray menu handlers
# ---------------------------------------------------------------------------
def on_open_webui(icon, item):
    if not _is_webui_running():
        start_webui()
    else:
        _log("WebUI already running.")


def on_restart_webui(icon, item):
    threading.Thread(target=restart_webui, daemon=True).start()


def on_open_config(icon, item):
    open_config_folder()


def on_exit(icon, item):
    _log("Exit requested.")
    icon.visible = False
    stop_webui()
    icon.stop()


# ---------------------------------------------------------------------------
# Icon factory
# ---------------------------------------------------------------------------
def _load_icon() -> Image.Image:
    if ICON_PATH.exists():
        return Image.open(ICON_PATH)
    img = Image.new("RGBA", (64, 64), (0, 120, 212, 255))
    return img


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------
def main():
    _log("AlasTray starting...")
    _log(f"ALAS_ROOT: {ALAS_ROOT}")

    # Step 1: Run installer (update check, pip install, etc.)
    if not run_installer():
        _log("AlasTray cannot continue due to installer failure.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Step 2: Start WebUI
    start_webui()

    # Step 3: Show tray icon
    icon = pystray.Icon(
        "AlasTray",
        icon=_load_icon(),
        title="AzurLaneAutoScript",
        menu=pystray.Menu(
            pystray.MenuItem("Open WebUI", on_open_webui),
            pystray.MenuItem("Restart WebUI", on_restart_webui),
            pystray.MenuItem("Open Config Folder", on_open_config),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", on_exit),
        ),
    )

    _log("Tray icon ready.")
    icon.run()
    _log("AlasTray exited.")


if __name__ == "__main__":
    main()
