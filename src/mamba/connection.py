"""Configured MAVSDK v4 discovery, availability, and connection lifecycle (F2)."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
import re
import tomllib
from typing import Literal
from urllib.parse import urlsplit

from mavsdk import LogLevel, log_subscribe, log_unsubscribe
from mavsdk.asyncio import ComponentType, Configuration, Mavsdk
from mavsdk.asyncio.system import System

DISCOVERY_TIMEOUT = 10.0
RETRY_INTERVAL = 5.0
POLL_INTERVAL = 1.0
LOGGER = logging.getLogger("mamba.connection")
ConnectionState = Literal[
    "unconfigured", "connecting", "connected", "disconnected", "error"
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class VehicleConfig:
    connection_url: str
    system_id: int

    @classmethod
    def load(cls, path: Path) -> "VehicleConfig":
        with path.open("rb") as stream:
            data = tomllib.load(stream)
        if set(data) != {"vehicle"} or not isinstance(data["vehicle"], dict):
            raise ValueError("Configuration must contain only a [vehicle] table")
        vehicle = data["vehicle"]
        if set(vehicle) != {"connection_url", "system_id"}:
            raise ValueError("[vehicle] requires only connection_url and system_id")
        system_id = vehicle["system_id"]
        if type(system_id) is not int or not 1 <= system_id <= 255:
            raise ValueError("system_id must be an integer from 1 to 255")
        url = vehicle["connection_url"]
        if not isinstance(url, str) or not url or any(c.isspace() for c in url):
            raise ValueError("connection_url must be a nonempty URL without whitespace")
        parts = urlsplit(url)
        if parts.scheme == "serial":
            if not re.fullmatch(r"serial://(?:/[^:]+|[^/:]+):[1-9][0-9]*", url):
                raise ValueError("Serial URL must specify a device and positive baud rate")
        elif parts.scheme in {"udpin", "udpout", "tcpin", "tcpout"}:
            if (not parts.hostname or parts.port is None or not 1 <= parts.port <= 65535
                    or parts.username is not None or parts.password is not None
                    or parts.path or parts.query or parts.fragment):
                raise ValueError("Network URL must contain a host and port (1-65535) only")
        else:
            raise ValueError("Supported URL schemes: udpin, udpout, tcpin, tcpout, serial")
        return cls(connection_url=url, system_id=system_id)


@dataclass
class VehicleStatus:
    system_id: int | None = None
    state: ConnectionState = "unconfigured"
    reason: str = "No vehicle configuration supplied"
    last_changed_at: str = ""
    last_checked_at: str | None = None
    discovered_system_ids: tuple[int, ...] = ()


class VehicleConnection:
    """Own one configured vehicle's SDK, discovery task, and availability state."""

    def __init__(self, config: VehicleConfig | None = None):
        self.config = config
        self.status = VehicleStatus(
            system_id=config.system_id if config else None,
            last_changed_at=utc_now(),
        )
        self.sdk: Mavsdk | None = None
        self.system: System | None = None
        self.generation = 0

    def set_state(self, state: ConnectionState, reason: str) -> None:
        if (state == "connected") != (self.status.state == "connected"):
            self.generation += 1
        if (state, reason) != (self.status.state, self.status.reason):
            self.status.state = state
            self.status.reason = reason
            self.status.last_changed_at = utc_now()
            LOGGER.info("Vehicle %s: %s (%s)", self.status.system_id, state, reason)

    async def find_vehicle(self) -> System | None:
        """Check all discovered systems; a different autopilot is never selected."""
        candidates = []
        ids = []
        for system in await self.sdk.get_systems():
            if await system.has_autopilot() and await system.is_connected():
                system_id = await system.get_system_id()
                ids.append(system_id)
                if system_id == self.config.system_id:
                    candidates.append(system)
        self.status.discovered_system_ids = tuple(sorted(ids))
        self.status.last_checked_at = utc_now()
        if len(candidates) > 1:
            raise RuntimeError("Multiple autopilots match the configured system ID")
        return candidates[0] if candidates else None

    async def run(self) -> None:
        """Keep the transport and SDK alive while rediscovering after link loss."""
        if self.config is None:
            return
        transport_added = False
        ever_connected = False
        setup_task: asyncio.Task | None = None
        try:
            while True:
                self.set_state("connecting", "Waiting for configured autopilot")
                try:
                    if self.sdk is None:
                        self.sdk = Mavsdk(Configuration.create_with_component_type(
                            ComponentType.GROUND_STATION
                        ))
                    if not transport_added:
                        if setup_task is None:
                            setup_task = asyncio.create_task(
                                self.sdk.add_any_connection(self.config.connection_url)
                            )
                        # Native setup runs in an executor and cannot be cancelled.
                        # Keep its task after a timeout to avoid opening duplicate links.
                        await asyncio.wait_for(
                            asyncio.shield(setup_task),
                            timeout=DISCOVERY_TIMEOUT,
                        )
                        transport_added = True
                        setup_task = None
                    deadline = asyncio.get_running_loop().time() + DISCOVERY_TIMEOUT
                    while True:
                        self.system = await self.find_vehicle()
                        if self.system is not None:
                            ever_connected = True
                            self.set_state("connected", "Configured autopilot is connected")
                        elif self.status.state == "connected":
                            self.set_state("disconnected", "Configured autopilot disconnected")
                            break
                        elif asyncio.get_running_loop().time() >= deadline:
                            state = "disconnected" if ever_connected else "error"
                            self.set_state(state, "Discovery timed out for configured system ID")
                            break
                        await asyncio.sleep(POLL_INTERVAL)
                except TimeoutError:
                    if setup_task is not None and setup_task.done():
                        setup_task = None
                    self.system = None
                    self.set_state("error", "MAVSDK connection timed out")
                except Exception as exc:
                    if setup_task is not None and setup_task.done():
                        setup_task = None
                    self.system = None
                    self.status.discovered_system_ids = ()
                    self.set_state("error", f"MAVSDK connection failure: {exc}")
                await asyncio.sleep(RETRY_INTERVAL)
        finally:
            self.system = None
            if self.status.state == "connected":
                self.set_state("disconnected", "Connection monitoring stopped")
            if setup_task is not None:
                # Do not destroy native handles while setup is still using them.
                with suppress(Exception):
                    await setup_task
            if self.sdk is not None:
                # Native teardown may wait for worker threads; keep MCP's loop responsive.
                await asyncio.to_thread(self.sdk.destroy)
                self.sdk = None


def sdk_log(level: LogLevel, message: str, file: str | None, line: int) -> bool:
    LOGGER.log({LogLevel.DEBUG: logging.DEBUG, LogLevel.INFO: logging.INFO,
                LogLevel.WARN: logging.WARNING, LogLevel.ERROR: logging.ERROR}[level],
               "%s", message)
    return True  # Suppress MAVSDK's default stdout logging.


@asynccontextmanager
async def vehicle_connection(
    config_path: Path | None = None,
) -> AsyncIterator[VehicleConnection]:
    """Load configuration and own discovery, native logging, and shutdown."""
    connection = VehicleConnection()
    if config_path is not None:
        try:
            connection = VehicleConnection(VehicleConfig.load(config_path))
        except (OSError, ValueError) as exc:
            connection.set_state("error", f"Invalid vehicle configuration: {exc}")
    log_subscribe(sdk_log)
    task = asyncio.create_task(connection.run(), name="vehicle-discovery")
    try:
        yield connection
    finally:
        task.cancel()
        try:
            with suppress(asyncio.CancelledError):
                await task
        finally:
            log_unsubscribe()
