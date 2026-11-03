"""MAMBA stdio tools and persistent, configured MAVSDK v4 discovery (F2)."""

import argparse
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import replace
import logging
from pathlib import Path
from typing import TypeVar

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError

if __package__:
    from .connection import VehicleStatus, vehicle_connection
    from . import vehicle_data
else:
    from connection import VehicleStatus, vehicle_connection
    import vehicle_data

Result = TypeVar("Result")


async def read_vehicle(
    ctx: Context,
    operation: Callable[[vehicle_data.VehicleData], Awaitable[Result]],
) -> Result:
    data = ctx.request_context.lifespan_context["vehicle_data"]
    try:
        return await operation(data)
    except vehicle_data.RetrievalError as exc:
        raise ToolError(str(exc)) from exc


def create_server(config_path: Path | None = None) -> FastMCP:
    @asynccontextmanager
    async def lifespan(server: FastMCP):
        async with vehicle_connection(config_path) as connection:
            async with vehicle_data.VehicleData(connection) as data:
                yield {"vehicle_connection": connection, "vehicle_data": data}

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

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_information(ctx: Context) -> vehicle_data.Reading[vehicle_data.InformationData]:
        """Read identification and software versions; report unavailable sections explicitly.

        received_at is MAMBA receipt time, not a sensor measurement timestamp.
        """
        return await read_vehicle(ctx, vehicle_data.VehicleData.information)

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_position(ctx: Context) -> vehicle_data.Reading[vehicle_data.PositionData]:
        """Read latitude/longitude (degrees), absolute AMSL and relative altitude (metres).

        received_at is MAMBA receipt time; the SDK may supply its latest stored state.
        """
        return await read_vehicle(ctx, vehicle_data.VehicleData.position)

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_velocity(ctx: Context) -> vehicle_data.Reading[vehicle_data.VelocityData]:
        """Read NED velocity in m/s; positive down_m_s points downward.

        received_at is MAMBA receipt time, not validated sensor freshness.
        """
        return await read_vehicle(ctx, vehicle_data.VehicleData.velocity)

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_battery(ctx: Context) -> vehicle_data.Reading[vehicle_data.BatteryData]:
        """Read one battery update: ID, V, A, degC, Ah, percent (0-100), and seconds.

        Unknown numeric values are null; received_at records MAMBA receipt time.
        """
        return await read_vehicle(ctx, vehicle_data.VehicleData.battery)

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_gps(ctx: Context) -> vehicle_data.Reading[vehicle_data.GpsData]:
        """Read satellite count and GPS fix type; received_at is MAMBA receipt time."""
        return await read_vehicle(ctx, vehicle_data.VehicleData.gps)

    @server.tool(annotations={"readOnlyHint": True})
    async def get_vehicle_health(ctx: Context) -> vehicle_data.Reading[vehicle_data.HealthData]:
        """Read SDK health/calibration and armability flags, including false values.

        Flags do not authorize actions; received_at is MAMBA receipt time.
        """
        return await read_vehicle(ctx, vehicle_data.VehicleData.health)

    return server


mcp = create_server()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Path to vehicle TOML configuration")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    create_server(args.config).run(transport="stdio")
