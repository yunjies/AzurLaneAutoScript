#!/usr/bin/env python3
"""
Alas Launcher (Python version)
Replaces the legacy Bat-To-Exe Alas.exe.

Usage:
    Double-click Alas.exe (built from this script via PyInstaller)

Flow:
    1. Find ALAS root directory
    2. Set up PATH (toolkit, Git, adb, etc.)
    3. Run deploy.installer (git update, pip install, adb install)
    4. Launch AlasTray.exe if available, otherwise fall back to webapp/alas.exe
"""

import os
import subprocess
import sys
from pathlib import Path


def find_alas_root() -> Path:
    """Derive ALAS root from this script's location."""
    # This file is at deploy/launcher/launcher.py
    return Path(__file__).resolve().parent.parent.parent


def setup_environment(root: Path) -> dict:
    """Build PATH env var exactly like Alas.bat does."""
    toolkit = root / "toolkit"
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


def find_python(env: dict, root: Path) -> str:
    """Find the Python executable to run deploy.installer."""
    # Prefer toolkit/python.exe if it exists
    toolkit_python = root / "toolkit" / "python.exe"
    if toolkit_python.exists():
        return str(toolkit_python)
    # Otherwise rely on PATH
    return "python"


def main():
    root = find_alas_root()
    env = setup_environment(root)
    python_exe = find_python(env, root)

    # Step 1: Run installer
    print("[Alas] Running installer...")
    result = subprocess.run(
        [python_exe, "-m", "deploy.installer"],
        cwd=str(root),
        env=env,
    )
    if result.returncode != 0:
        print("[Alas] Installer failed. Press Enter to exit...")
        input()
        sys.exit(1)

    # Step 2: Launch tray or webapp
    tray_exe = root / "toolkit" / "AlasTray" / "AlasTray.exe"
    webapp_exe = root / "toolkit" / "webapp" / "alas.exe"

    target = tray_exe if tray_exe.exists() else webapp_exe
    if not target.exists():
        print(f"[Alas] ERROR: Neither AlasTray nor WebUI found.")
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"[Alas] Starting {target.name}...")
    subprocess.Popen(
        [str(target)],
        cwd=str(target.parent),
        env=env,
    )


if __name__ == "__main__":
    main()
