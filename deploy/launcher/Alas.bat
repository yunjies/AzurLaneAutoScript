@rem
@echo off

set "_root=%~dp0"
set "_root=%_root:~0,-1%"
cd "%_root%"

color F0

:: Alas.exe is the single entry point — it runs installer internally
:: and then starts WebUI + system tray.
if exist "%_root%\Alas.exe" (
    start "Alas" "%_root%\Alas.exe"
) else (
    echo ERROR: Alas.exe not found. Please build it first:
    echo   .venv\Scripts\python.exe deploy\tray\build.py
    pause >nul
)
