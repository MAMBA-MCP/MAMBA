"""MAMBA stdio tools and persistent, configured MAVSDK v4 discovery (F2)."""

import argparse
from contextlib import asynccontextmanager
from dataclasses import replace
import logging
from pathlib import Path

from fastmcp import Context, FastMCP

if __package__:
    from .connection import VehicleStatus, vehicle_connection
else:
    from connection import VehicleStatus, vehicle_connection


def create_server(config_path: Path | None = None) -> FastMCP:
    @asynccontextmanager
    async def lifespan(server: FastMCP):
        async with vehicle_connection(config_path) as connection:
            yield {"vehicle_connection": connection}

    server = FastMCP("MAMBA", lifespan=lifespan)

    @server.tool
    def ping() -> str:
        """Check that the MAMBA MCP server is responding."""
        return "pong"

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_status(ctx: Context) -> VehicleStatus:
        """Return configured vehicle availability, identity, and UTC observation times.

        Connection state alone does not establish vehicle health or permission to act.
        """
        connection = ctx.request_context.lifespan_context["vehicle_connection"]
        return replace(connection.status)

    return server


mcp = create_server()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Path to vehicle TOML configuration")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    create_server(args.config).run(transport="stdio")
