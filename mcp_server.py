"""
ALAS MCP Server  v0.1.0
Exposes ALAS REST API as MCP Tools.

Supports both stdio (local AI assistant) and SSE (remote/phone) transports.

Usage (stdio - for Claude Desktop / WorkBuddy):
  python mcp_server.py

Usage (SSE - for remote access):
   python mcp_server.py --transport sse --port 8080
   Then configure AI assistant to connect to http://<your-pc-ip>:8080/sse

Environment:
  ALAS_API_BASE  - ALAS API address (default http://127.0.0.1:22267)
  ALAS_API_KEY   - (reserved for future auth)
"""

import argparse
import asyncio
import json
import os
import sys

import httpx
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
ALAS_API_BASE = os.getenv("ALAS_API_BASE", "http://127.0.0.1:22267")
TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
async def api_get(path: str) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(f"{ALAS_API_BASE}{path}")
        r.raise_for_status()
        return r.json()


async def api_put(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.put(f"{ALAS_API_BASE}{path}", json=body)
        r.raise_for_status()
        return r.json()


async def api_post(path: str, body: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.post(f"{ALAS_API_BASE}{path}", json=body)
        r.raise_for_status()
        return r.json()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------
server = Server("alas-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="alas_list_instances",
            description="列出所有 ALAS 实例（配置组别），返回名称和配置路径。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="alas_get_config",
            description="获取指定实例的完整配置。instance 为实例名，如 'alas'。",
            inputSchema={
                "type": "object",
                "properties": {"instance": {"type": "string", "description": "实例名，如 'alas'"}},
                "required": ["instance"],
            },
        ),
        Tool(
            name="alas_update_config",
            description="修改实例的配置项。updates 为 key-value 字典，如 {\"Emotion_RestStrict\": true}。",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "实例名"},
                    "updates": {"type": "object", "description": "要更新的配置键值对"},
                },
                "required": ["instance", "updates"],
            },
        ),
        Tool(
            name="alas_get_status",
            description="获取实例运行状态（是否存活、进程PID等）。",
            inputSchema={
                "type": "object",
                "properties": {"instance": {"type": "string", "description": "实例名"}},
                "required": ["instance"],
            },
        ),
        Tool(
            name="alas_get_log",
            description="获取实例最近日志。lines 控制行数（默认50）。",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "实例名"},
                    "lines": {"type": "integer", "description": "行数，默认50", "default": 50},
                },
                "required": ["instance"],
            },
        ),
        Tool(
            name="alas_screenshot",
            description="对模拟器截图，返回截图文件路径（ALAS 所在机器上的路径）。",
            inputSchema={
                "type": "object",
                "properties": {"instance": {"type": "string", "description": "实例名"}},
                "required": ["instance"],
            },
        ),
        Tool(
            name="alas_start",
            description="启动指定实例（开始调度循环）。",
            inputSchema={
                "type": "object",
                "properties": {"instance": {"type": "string", "description": "实例名"}},
                "required": ["instance"],
            },
        ),
        Tool(
            name="alas_stop",
            description="停止指定实例（优雅退出）。",
            inputSchema={
                "type": "object",
                "properties": {"instance": {"type": "string", "description": "实例名"}},
                "required": ["instance"],
            },
        ),
        Tool(
            name="alas_run_task",
            description="让实例运行一次指定任务，如 'Battle'、'Commission'、'Research'。",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance": {"type": "string", "description": "实例名"},
                    "task": {"type": "string", "description": "任务名，如 'Battle'"},
                },
                "required": ["instance", "task"],
            },
        ),
        Tool(
            name="alas_check_update",
            description="检查 ALAS 是否有可用更新（对比 git remote）。",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="alas_perform_update",
            description="【危险】执行 ALAS 自更新（git pull + pip install），会重启 ALAS。仅在用户明确要求时调用。",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "alas_list_instances":
            data = await api_get("/api/instances")
            instances = data.get("instances", [])
            if not instances:
                return [TextContent(type="text", text="没有找到实例。")]
            lines = [f"• {i['name']}  (配置: {i['config_path']})" for i in instances]
            return [TextContent(type="text", text="\n".join(lines))]

        elif name == "alas_get_config":
            inst = arguments["instance"]
            data = await api_get(f"/api/instances/{inst}/config")
            text = json.dumps(data, indent=2, ensure_ascii=False)
            if len(text) > 8000:
                text = text[:8000] + "\n...(已截断，请指定具体 key 查询)"
            return [TextContent(type="text", text=text)]

        elif name == "alas_update_config":
            inst = arguments["instance"]
            updates = arguments["updates"]
            result = await api_put(f"/api/instances/{inst}/config", updates)
            return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]

        elif name == "alas_get_status":
            inst = arguments["instance"]
            data = await api_get(f"/api/instances/{inst}/status")
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "alas_get_log":
            inst = arguments["instance"]
            lines = arguments.get("lines", 50)
            data = await api_get(f"/api/instances/{inst}/log?lines={lines}")
            return [TextContent(type="text", text=data.get("log", "(无日志输出)"))]

        elif name == "alas_screenshot":
            inst = arguments["instance"]
            data = await api_get(f"/api/instances/{inst}/screenshot")
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "alas_start":
            inst = arguments["instance"]
            data = await api_post(f"/api/instances/{inst}/start")
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "alas_stop":
            inst = arguments["instance"]
            data = await api_post(f"/api/instances/{inst}/stop")
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "alas_run_task":
            inst = arguments["instance"]
            task = arguments["task"]
            data = await api_post(f"/api/instances/{inst}/run", {"task": task})
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "alas_check_update":
            data = await api_get("/api/update/check")
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        elif name == "alas_perform_update":
            data = await api_post("/api/update/run", {})
            return [TextContent(type="text", text=json.dumps(data, indent=2, ensure_ascii=False))]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    except httpx.HTTPStatusError as e:
        return [TextContent(type="text", text=f"HTTP 错误 {e.response.status_code}: {e.response.text[:500]}")]
    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]


# ---------------------------------------------------------------------------
# Transport entry points
# ---------------------------------------------------------------------------
async def run_stdio():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run_sse(host: str = "0.0.0.0", port: int = 8080):
    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request.send) as (
            read_stream, write_stream,
        ):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    app = Starlette(
        routes=[
            Route("/sse", handle_sse),
            Mount("/messages", app=sse.handle_post_message),
        ],
    )
    print(f"[MCP SSE] Listening on http://{host}:{port}/sse")
    uvicorn.run(app, host=host, port=port)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ALAS MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "sse"], default="stdio",
        help="Transport mode: stdio (local) or sse (remote). Default: stdio",
    )
    parser.add_argument("--host", default="0.0.0.0", help="SSE listen host (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="SSE listen port (default 8080)")
    args = parser.parse_args()

    if args.transport == "stdio":
        print("[MCP] Starting in stdio mode...", flush=True)
        asyncio.run(run_stdio())
    else:
        run_sse(args.host, args.port)
