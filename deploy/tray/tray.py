#!/usr/bin/env python3
r"""
Alas — All-in-one launcher + system tray for AzurLaneAutoScript

Usage:
    Double-click Alas.exe (or Alas.bat)

Flow:
    1. Find ALAS root directory
    2. Set up PATH (toolkit, Git, adb, etc.)
    3. Run deploy.installer (git update, pip install, adb install)
    4. Start Python WebUI backend (gui.py via toolkit/python.exe)
    5. Start Electron desktop app (optional, wraps the WebUI)
    6. Show system tray icon (常驻)

Note:
    Built with --windowed (no console), so NEVER use input() or
    print-to-stderr expecting user to see it.  Use ctypes.MessageBox
    for critical errors instead.
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
#
# When running as a PyInstaller exe, __file__ points to a temp extraction
# directory, so we CANNOT use it to find ALAS_ROOT.  Instead, we use
# sys.executable (the path to Alas.exe itself) which lives in ALAS_ROOT.
# ---------------------------------------------------------------------------
def _resolve_alas_root() -> Path:
    """Resolve ALAS root directory.

    - PyInstaller exe: sys.executable = E:\\...\\Alas.exe  → parent = ALAS_ROOT
    - Python script:   __file__ = .../deploy/tray/tray.py  → parent.parent.parent
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle — exe is in ALAS root
        return Path(sys.executable).parent.resolve()
    else:
        # Running as Python script
        return Path(__file__).parent.parent.parent.resolve()


ALAS_ROOT = _resolve_alas_root()
ICON_PATH = ALAS_ROOT / "deploy" / "launcher" / "icon.ico"
WEBAPP_PATH = ALAS_ROOT / "toolkit" / "webapp" / "alas.exe"
CONFIG_DIR = ALAS_ROOT / "config"

# ---------------------------------------------------------------------------
# Process state
# ---------------------------------------------------------------------------
_backend_proc = None   # Python WebUI backend (gui.py)
_electron_proc = None  # Electron desktop wrapper (optional)
_lock = threading.Lock()


def _log(msg: str):
    """Log to file; avoid stdout/stderr in windowed mode."""
    log_path = ALAS_ROOT / "log" / "alas_tray.log"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            from datetime import datetime
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except Exception:
        pass


def _show_error(title: str, message: str):
    """Show a Windows MessageBox (works in --windowed mode)."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        pass


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


def _read_webui_port() -> str:
    """Read WebuiPort from config/deploy.yaml (default 22267)."""
    import re
    deploy_yaml = ALAS_ROOT / "config" / "deploy.yaml"
    if deploy_yaml.exists():
        try:
            text = deploy_yaml.read_text(encoding="utf-8")
            m = re.search(r"WebuiPort:\s*(\d+)", text)
            if m:
                return m.group(1)
        except Exception:
            pass
    return "22267"


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


# ---------------------------------------------------------------------------
# Python backend management
# ---------------------------------------------------------------------------
def _is_backend_running() -> bool:
    """Check if the Python backend process is still alive."""
    global _backend_proc
    if _backend_proc is None:
        return False
    return _backend_proc.poll() is None


def start_backend():
    """Start the Python WebUI backend (gui.py)."""
    global _backend_proc
    with _lock:
        if _is_backend_running():
            _log("Backend is already running.")
            return
        env = _setup_env()
        python_exe = _find_python(env)
        port = _read_webui_port()

        cmd = [python_exe, "gui.py", "--port", port]
        _log(f"Starting backend: {' '.join(cmd)}")
        _backend_proc = subprocess.Popen(
            cmd,
            cwd=str(ALAS_ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        _log(f"Backend started (pid={_backend_proc.pid})")


def stop_backend():
    """Stop the Python WebUI backend."""
    global _backend_proc
    with _lock:
        if _backend_proc is None:
            return
        _log(f"Stopping backend (pid={_backend_proc.pid})...")
        try:
            _backend_proc.terminate()
            try:
                _backend_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _log("Backend did not exit gracefully, forcing kill...")
                _backend_proc.kill()
                _backend_proc.wait()
        except ProcessLookupError:
            pass
        except Exception as e:
            _log(f"Error stopping backend: {e}")
        finally:
            _backend_proc = None
        _log("Backend stopped.")


def restart_backend():
    """Restart the Python WebUI backend."""
    _log("Restarting backend...")
    stop_backend()
    time.sleep(0.5)
    start_backend()


# ---------------------------------------------------------------------------
# Electron app management
# ---------------------------------------------------------------------------
def _is_electron_running() -> bool:
    """Check if the Electron app process is still alive."""
    global _electron_proc
    if _electron_proc is None:
        return False
    return _electron_proc.poll() is None


def start_electron():
    """Start the Electron desktop wrapper (optional)."""
    global _electron_proc
    with _lock:
        if _is_electron_running():
            _log("Electron is already running.")
            return
        if not WEBAPP_PATH.exists():
            _log(f"Electron app not found at {WEBAPP_PATH}, skipping.")
            return
        _log(f"Starting Electron: {WEBAPP_PATH}")
        _electron_proc = subprocess.Popen(
            [str(WEBAPP_PATH)],
            cwd=str(ALAS_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        _log(f"Electron started (pid={_electron_proc.pid})")


def stop_electron():
    """Stop the Electron desktop wrapper."""
    global _electron_proc
    with _lock:
        if _electron_proc is None:
            return
        _log(f"Stopping Electron (pid={_electron_proc.pid})...")
        try:
            _electron_proc.terminate()
            try:
                _electron_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _electron_proc.kill()
                _electron_proc.wait()
        except ProcessLookupError:
            pass
        except Exception as e:
            _log(f"Error stopping Electron: {e}")
        finally:
            _electron_proc = None
        _log("Electron stopped.")


# ---------------------------------------------------------------------------
# Convenience: start/stop everything
# ---------------------------------------------------------------------------
def start_webui():
    """Start backend + Electron."""
    start_backend()
    # Give the backend a moment to start listening before Electron connects
    time.sleep(2)
    start_electron()


def stop_webui():
    """Stop Electron + backend."""
    stop_electron()
    stop_backend()


def restart_webui():
    """Restart everything."""
    _log("Restarting WebUI...")
    stop_electron()
    restart_backend()
    time.sleep(2)
    start_electron()


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
    if not _is_backend_running():
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
    return Image.new("RGBA", (64, 64), (0, 120, 212, 255))


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------
def main():
    _log("Alas starting...")
    _log(f"ALAS_ROOT: {ALAS_ROOT}")

    # Step 1: Run installer (update check, pip install, etc.)
    if not run_installer():
        _log("Alas cannot continue due to installer failure.")
        _show_error("Alas - Installer Failed",
                     "The ALAS installer failed to complete.\n"
                     "Check log/alas_tray.log for details.")
        sys.exit(1)

    # Step 2: Start WebUI (Python backend + Electron wrapper)
    start_webui()

    # Step 3: Show tray icon
    icon = pystray.Icon(
        "Alas",
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
    _log("Alas exited.")


if __name__ == "__main__":
    main()
