#!/usr/bin/env python3
"""
Build script for Alas.exe (launcher)

Usage:
    cd E:\AzurLaneAutoScript
    .venv\Scripts\python.exe deploy\launcher\build.py

Output:
    Alas.exe  (replaces the one in ALAS root)
"""

import subprocess
import sys
from pathlib import Path

LAUNCHER_DIR = Path(__file__).parent.resolve()
ALAS_ROOT = LAUNCHER_DIR.parent.parent.resolve()
ICON_PATH = LAUNCHER_DIR / "icon.ico"
LAUNCHER_PY = LAUNCHER_DIR / "launcher.py"
OUTPUT_DIR = ALAS_ROOT  # Place Alas.exe directly in ALAS root

PYTHON_EXE = ALAS_ROOT / ".venv" / "Scripts" / "python.exe"


def main():
    if not PYTHON_EXE.exists():
        print(f"ERROR: Python not found at {PYTHON_EXE}")
        sys.exit(1)
    if not LAUNCHER_PY.exists():
        print(f"ERROR: launcher.py not found at {LAUNCHER_PY}")
        sys.exit(1)
    if not ICON_PATH.exists():
        print(f"WARNING: Icon not found at {ICON_PATH}")
        icon_arg = []
    else:
        icon_arg = ["--icon", str(ICON_PATH)]

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "Alas",
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(ALAS_ROOT / "toolkit" / "AlasLauncher_build"),
        "--specpath", str(ALAS_ROOT / "toolkit" / "AlasLauncher_build"),
    ] + icon_arg + [str(LAUNCHER_PY)]

    print("Building Alas.exe...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=str(ALAS_ROOT))
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(result.returncode)

    exe_path = OUTPUT_DIR / "Alas.exe"
    if exe_path.exists():
        print(f"\nSUCCESS: {exe_path}")
        print("You can now double-click Alas.exe to launch ALAS with tray support.")
    else:
        print(f"\nWARNING: Expected output not found at {exe_path}")


if __name__ == "__main__":
    main()
