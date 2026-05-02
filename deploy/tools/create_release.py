#!/usr/bin/env python3
"""
Auto-create GitHub Release.

Usage:
    cd E:\AzurLaneAutoScript
    .venv\Scripts\python.exe deploy\tools\create_release.py --token YOUR_GITHUB_TOKEN

Or set token via env:
    set GITHUB_TOKEN=ghp_xxx
    .venv\Scripts\python.exe deploy\tools\create_release.py
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

OWNER = "yunjies"
REPO = "AzurLaneAutoScript"
TAG = "v0.1.0"
RELEASE_NAME = "v0.1.0 — MCP Server Integration"
RELEASE_BODY = """## What's New

### MCP Server Integration
- 11 MCP tools for AI control (instances, tasks, config, screenshots, logs)
- **stdio transport** for local AI (WorkBuddy, Claude Desktop, Cursor)
- **SSE transport** for remote/web access at `/mcp/sse`

### REST API (Phase 1)
- 11 API endpoints: configuration, status, logs, screenshots, start/stop
- CORS enabled for cross-origin access

### MCP Settings Page (WebUI)
- New "MCP" sidebar button
- Shows server status, available tools, and configuration guides

Full changelog: [CHANGELOG.md](https://github.com/yunjies/AzurLaneAutoScript/blob/master/CHANGELOG.md)
"""

# No binary assets — users run Alas.bat or toolkit/webapp/alas.exe directly
ASSETS = []


def create_release(token: str, draft: bool = False, prerelease: bool = False):
    """Create GitHub release."""
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/releases"
    data = json.dumps({
        "tag_name": TAG,
        "name": RELEASE_NAME,
        "body": RELEASE_BODY,
        "draft": draft,
        "prerelease": prerelease,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print(f"Creating release {TAG}...")
    with urllib.request.urlopen(req) as resp:
        release = json.loads(resp.read().decode())
        upload_url = release["upload_url"].replace("{?name,label}", "")
        html_url = release["html_url"]
        print(f"  Created: {html_url}")

    # Upload assets
    for label, filepath in ASSETS:
        if not filepath.exists():
            print(f"  WARNING: {filepath} not found, skipping")
            continue

        asset_url = f"{upload_url}?name={label}"
        print(f"  Uploading {label} ({filepath.stat().st_size / 1024 / 1024:.1f} MB)...")

        with open(filepath, "rb") as f:
            asset_data = f.read()

        req = urllib.request.Request(
            asset_url,
            data=asset_data,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/octet-stream",
            },
            method="POST",
        )

        with urllib.request.urlopen(req) as resp:
            print(f"    OK: {json.loads(resp.read())['browser_download_url']}")

    print(f"\nDone! Release URL: {html_url}")


def main():
    parser = argparse.ArgumentParser(description="Create GitHub release for ALAS")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub personal access token")
    parser.add_argument("--draft", action="store_true", help="Create as draft")
    parser.add_argument("--prerelease", action="store_true", help="Create as pre-release")
    args = parser.parse_args()

    if not args.token:
        print("ERROR: GitHub token required. Use --token or set GITHUB_TOKEN env.")
        print("Create token at: https://github.com/settings/tokens")
        print("Required scope: 'repo'")
        sys.exit(1)

    create_release(args.token, args.draft, args.prerelease)


if __name__ == "__main__":
    main()
