#!/usr/bin/env python3
"""
Build script for AlasTray.exe

Usage:
    cd E:\AzurLaneAutoScript
    .venv\Scripts\python.exe deploy\tray\build.py

Output:
    toolkit/AlasTray/AlasTray.exe
"""

import subprocess
import sys
from pathlib import Path

TRAY_DIR = Path(__file__).parent.resolve()
ALAS_ROOT = TRAY_DIR.parent.parent.resolve()
ICON_PATH = ALAS_ROOT / "deploy" / "launcher" / "icon.ico"
TRAY_PY = TRAY_DIR / "tray.py"
OUTPUT_DIR = ALAS_ROOT / "toolkit" / "AlasTray"

PYTHON_EXE = ALAS_ROOT / ".venv" / "Scripts" / "python.exe"


def main():
    if not PYTHON_EXE.exists():
        print(f"ERROR: Python not found at {PYTHON_EXE}")
        sys.exit(1)
    if not TRAY_PY.exists():
        print(f"ERROR: tray.py not found at {TRAY_PY}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(PYTHON_EXE),
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", "AlasTray",
        "--icon", str(ICON_PATH),
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(OUTPUT_DIR / "build"),
        "--specpath", str(OUTPUT_DIR),
        str(TRAY_PY),
    ]

    print("Building AlasTray.exe...")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=str(ALAS_ROOT))
    if result.returncode != 0:
        print("Build failed!")
        sys.exit(result.returncode)

    exe_path = OUTPUT_DIR / "AlasTray.exe"
    if exe_path.exists():
        print(f"\nSUCCESS: {exe_path}")
    else:
        print(f"\nWARNING: Expected output not found at {exe_path}")


if __name__ == "__main__":
    main()
