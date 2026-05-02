# Release Guide

## Quick Release (One Command)

```batch
cd E:\AzurLaneAutoScript
set GITHUB_TOKEN=ghp_xxxxxxxxxxxx
.venv\Scripts\python.exe deploy\tools\create_release.py
```

That's it. The script will:
1. Create release `v0.1.0` on GitHub
2. Upload `Alas.exe` and `AlasTray.exe` as assets
3. Print the release URL

## Prerequisites

1. **Push commits first**:
   ```batch
   git push origin master
   git push origin v0.1.0
   ```

2. **Get a GitHub token**:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Check scope: `repo`
   - Copy the token (starts with `ghp_`)

## Manual Release (Web UI)

If you prefer the web interface:

1. Visit https://github.com/yunjies/AzurLaneAutoScript/releases/new
2. Tag: `v0.1.0`
3. Title: `v0.1.0 — AlasTray + MCP Server`
4. Body: copy from `CHANGELOG.md`
5. Upload `Alas.exe` and `toolkit/AlasTray/AlasTray.exe`
6. Click "Publish release"
