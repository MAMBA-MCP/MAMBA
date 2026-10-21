"""Minimal MAMBA MCP server using the official Python SDK v2."""

from mcp.server import MCPServer

mcp = MCPServer("MAMBA")


@mcp.tool()
def ping() -> str:
    """Check that the MAMBA MCP server is responding."""
    return "pong"


if __name__ == "__main__":
    mcp.run(transport="stdio")
