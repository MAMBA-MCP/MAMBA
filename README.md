# MAMBA

MCP-enabled Autonomous MAVLink-M Bridge for AI.

MAMBA is a Python MCP server for connecting AI agents to MAVLink vehicles. Its planned architecture routes vehicle commands through a deterministic safety layer before MAVSDK/protocol adapters execute them. MAVLink-M payload support remains planned.

## Current status

The server uses **FastMCP 2**, stdio transport, and the native **MAVSDK v4 asyncio API** (`mavsdk.asyncio`). It implements:

- `ping` to check MCP responsiveness.
- Optional startup discovery for one configured vehicle, selected by its expected MAVLink system ID.
- A persistent MAVSDK connection with background disconnect detection and recovery.
- Read-only connection status through `get_vehicle_status`.

This provides the connection and availability implementation for **MAMBA-2 / F2 — MAVSDK Drone Connection**. Automated tests cover configuration, identity selection, failures, recovery, and MCP integration. Successful ArduPilot discovery and disconnect acceptance remain pending SITL validation.

Vehicle telemetry/navigation tools, deterministic safety enforcement, authorization, multi-vehicle routing, simulator integration, and hardware validation remain planned. The [proposal](<Mamba(revised).pdf>) is the requirements baseline; its original dates are planning targets, not completion claims.

## Quick start

Use Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/). From the repository root:

```bash
uv sync --locked
uv run --locked python src/mamba/server.py
```

The server waits for MCP messages on stdin; stdout carries protocol traffic and diagnostics go to stderr. An MCP client discovers and calls its tools. Without `--config`, `ping` returns `pong` and vehicle status is `unconfigured`.

## Configure vehicle discovery

Select the [example configuration](config/vehicle.example.toml) explicitly, or copy it to a local file and edit it for your vehicle:

```toml
[vehicle]
connection_url = "udpin://127.0.0.1:14540"
system_id = 1
```

```bash
uv run --locked python src/mamba/server.py --config config/vehicle.example.toml
```

Configure the vehicle or SITL instance to send MAVLink to the specified endpoint. `system_id` must match the vehicle's MAVLink system ID (`SYSID_THISMAV` in ArduPilot) and be an integer from 1 to 255. Other discovered autopilots are never selected in place of the configured target. Restart MAMBA after editing its configuration.

Discovery has a 10-second timeout, a 5-second retry delay, and a 1-second polling interval. Disconnect detection also depends on MAVSDK's heartbeat timeout. Invalid configuration or connection failures appear in vehicle status while the MCP server remains available.

See the [connection runbook](docs/runbooks/connection.md) for the full schema, supported UDP/TCP/serial URL formats, status fields, SITL and physical connection examples, and validation limits. The example file is opt-in and has not been validated against SITL or hardware.

## Connect an MCP client

Configure a client that supports local stdio servers to launch MAMBA using absolute paths. A typical configuration is:

```json
{
  "mcpServers": {
    "MAMBA": {
      "command": "/absolute/path/to/uv",
      "args": [
        "run", "--locked",
        "--project", "/absolute/path/to/MAMBA",
        "python", "/absolute/path/to/MAMBA/src/mamba/server.py",
        "--config", "/absolute/path/to/vehicle.toml"
      ]
    }
  }
}
```

Adapt the configuration wrapper to your client. Omit `--config` and its path to run without vehicle discovery. The client manages the server subprocess; stop a manually launched server with Ctrl+C.

| Tool | Arguments | Result |
| --- | --- | --- |
| `ping` | `{}` | `pong` |
| `get_vehicle_status` | `{}` | Configured ID, connection state, reason, UTC observation/change timestamps, and discovered autopilot IDs |

Connection states are `unconfigured`, `connecting`, `connected`, `disconnected`, and `error`. Connection status does not establish vehicle health or authorization to execute actions.

## Development and validation

```bash
uv run --locked pytest -q
git diff --check
```

Tests cover configuration validation, matching/nonmatching IDs, multiple systems, transport/SDK errors, timeout, persistence, disconnect/recovery, and shutdown. Stdio integration tests also exercise the real native SDK on an empty loopback UDP endpoint. These checks establish timeout handling and protocol compatibility; ArduPilot SITL and physical vehicle acceptance remain pending.

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`. Use `uv add <dependency>` or `uv add --dev <dependency>` and commit the manifest and lockfile together. No formatter, linter, or coverage threshold is configured. See [development setup](docs/development.md) for environment details and recorded validation evidence.

Complete applicable simulation validation before incremental hardware testing; follow the [hardware runbook](docs/runbooks/hardware.md).

## Repository and documentation

| Location | Contents |
| --- | --- |
| [src/mamba/server.py](src/mamba/server.py) | FastMCP setup, tools, and CLI startup |
| [src/mamba/connection.py](src/mamba/connection.py) | Connection configuration, discovery, availability, and SDK lifecycle |
| [config/](config/README.md) | Connection example and reserved vehicle/payload safety definitions |
| [tests/](tests/README.md) | Unit and stdio integration tests; reserved simulation/hardware tests |
| [simulation/](simulation/README.md) | Reserved simulation scenarios and assets |
| [benchmarks/](benchmarks/README.md) | Reserved benchmark scenarios and assets |
| [docs/](docs/README.md) | Requirements, architecture, runbooks, and acceptance records |

Contributors should start with [AGENTS.md](AGENTS.md), the [architecture](docs/architecture.md), and the [requirements and roadmap](docs/requirements.md). Track unresolved choices in [open decisions](docs/decisions.md), and map implementation evidence to the [acceptance matrix](docs/testing/acceptance-matrix.md) and [safety requirements](docs/safety.md).

## License

[MIT](LICENSE).
