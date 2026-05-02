"""
ALAS MCP Server — core Server instance with tool registration.

This module creates a low-level mcp.server.Server so it can be wired into
both stdio and SSE transports without starting its own event loop.
"""
from mcp.server import Server
from mcp.types import TextContent, Tool

from module.mcp.tools import TOOL_SCHEMAS, TOOL_MAP

mcp_server = Server("alas")


@mcp_server.list_tools()
async def handle_list_tools() -> list:
    """Return all available ALAS tools."""
    return [Tool(**schema) for schema in TOOL_SCHEMAS]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """Execute an ALAS tool by name."""
    if name not in TOOL_MAP:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    func = TOOL_MAP[name]
    try:
        result = func(**arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return [TextContent(type="text", text=f"Error: {e}\n{tb}")]
