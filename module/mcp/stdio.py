"""
ALAS MCP Server — stdio transport entry point.

Usage:
    cd E:\AzurLaneAutoScript
    .venv\Scripts\python.exe -m module.mcp.stdio

This connects to Claude Desktop, Cursor, or any MCP client that speaks stdio.
"""
import asyncio

from module.mcp.server import mcp_server


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
