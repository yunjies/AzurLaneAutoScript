@echo off
echo Syncing upstream changes...
cd /d "%~dp0"
call .venv\Scripts\activate.bat
git pull upstream master
git push origin master
echo Done.
pause
