# Vehicle connection — MAMBA-2 / F2

MAMBA discovers one configured autopilot using the native MAVSDK v4 asyncio binding. `src/mamba/connection.py` owns configuration, status, discovery, SDK logging, and cleanup; `server.py` exposes the tools and starts FastMCP. A single SDK instance and transport persist across MCP calls and ordinary disconnects. The connection status tool exposes availability. Separate [vehicle data tools](vehicle-data.md) retrieve identification/version, position, NED velocity, battery, GPS, and health. These observations do not authorize actions. Safety enforcement, navigation, and multi-vehicle routing remain planned.

## Configuration and launch

Without `--config`, MAMBA runs with `ping` and an `unconfigured` vehicle status:

```bash
uv run --locked python src/mamba/server.py
```

Select the opt-in example explicitly, or copy it to a machine-local file and edit it:

```bash
uv run --locked python src/mamba/server.py --config config/vehicle.example.toml
```

For an MCP client, use the absolute uv executable and arguments `run --locked --project /absolute/path/to/MAMBA python /absolute/path/to/MAMBA/src/mamba/server.py --config /absolute/path/to/vehicle.toml`. Configuration paths resolve against the process working directory. Configuration is loaded once; restart MAMBA after editing it.

The TOML file must contain exactly one `[vehicle]` table, with exactly `connection_url` (string) and `system_id` (integer, 1–255). Booleans are rejected as IDs. Missing files, invalid TOML, unsupported URLs, and invalid fields produce an `error` status while `ping` remains available. An omitted file produces `unconfigured`.

```toml
[vehicle]
connection_url = "udpin://127.0.0.1:14540"
system_id = 1
```

The implementation accepts the native SDK's `udpin`, `udpout`, `tcpin`, `tcpout`, and `serial` schemes. Network URLs require an explicit host and port (1–65535), without credentials, paths, queries, or fragments; serial URLs require a device and positive baud rate. SDK errors such as an occupied port or missing device are reported through status and retried. Only loopback UDP startup/no-vehicle timeout has been exercised with the real SDK here; other methods require environment-specific validation. See [MAVSDK connection formats](https://mavsdk.mavlink.io/main/en/cpp/guide/connections.html) and the [v4 Python migration guide](https://mavsdk.mavlink.io/v4/en/python/migration.html).

## Discovery and status

Call `get_vehicle_status` with `{}`. It has no vehicle commands or configurable endpoint arguments. It returns:

| Field | Meaning |
| --- | --- |
| `system_id` | Configured MAVLink system ID; null if configuration was absent/invalid |
| `state` | `unconfigured`, `connecting`, `connected`, `disconnected`, or `error` |
| `reason` | Explanation of the current state or failure |
| `last_changed_at` | UTC ISO 8601 timestamp when the state or reason last changed |
| `last_checked_at` | UTC timestamp of the last completed discovery scan; null before a scan |
| `discovered_system_ids` | IDs of currently connected autopilots from the latest successful scan |

Discovery runs in a background task. Only a connected autopilot with the configured ID is selected; other systems remain visible through `discovered_system_ids`. MAVLink system IDs are routing identifiers, not authenticated identity. Duplicate IDs on a MAVLink network can be merged by the SDK and cannot reliably establish distinct physical identities. Ensure each system on the link has a unique ID.

The initial discovery window is 10 seconds. A missing target reports `error` with a timeout reason; a previously observed target reports `disconnected` after loss. Connection state is polled every second, in addition to the SDK's heartbeat loss detection delay. Following a failure or disconnection, discovery is retried after 5 seconds. A recovered matching target reports `connected`; unrelated autopilots are never substituted. Successful transport setup is retained during discovery retries. Connection setup also has a 10-second status timeout; if native setup is still running in its executor, retries await the same operation rather than adding duplicate links. Native SDK logs are redirected to stderr so stdout carries only MCP traffic.

Connection and SDK failures do not require MCP tool calls to retry. Configuration errors require an edited file and server restart. Stop the MCP client to close its subprocess, or use Ctrl+C for a manually launched server; shutdown cancels monitoring, waits for any in-flight native connection setup, and destroys the SDK. Native connection setup cannot be forcibly cancelled by asyncio.

## ArduPilot SITL acceptance — pending

Prerequisite: a separately installed, running ArduPilot SITL/MAVProxy environment. This repository does not install or launch SITL. Follow the official [SITL guide](https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html). In MAVProxy, use `output add 127.0.0.1:14540` to send MAVLink to the example's listener. Check `output` and confirm the vehicle's `SYSID_THISMAV` matches `system_id`. The example port is a deliberate destination, not an assumption about ArduPilot's default output.

1. Start SITL and its MAVLink output, then launch MAMBA with the matching TOML file.
2. Through an MCP client, call `ping` and `get_vehicle_status`; wait for the configured ID to become `connected`.
3. Call status repeatedly and confirm the connection persists between calls.
4. Stop SITL or remove the MAVProxy output. Record the time to `disconnected`, including the SDK's heartbeat delay; confirm `ping` still returns `pong`.
5. Restore the same target/output and verify recovery without restarting MAMBA. Introduce another uniquely identified system and verify it cannot replace the configured target.
6. Record firmware/version, SDK version, host, URI/port, IDs, commands, transition timestamps, and pass/fail evidence. Stop MAMBA and SITL and remove temporary output routing.

## Physical connection configuration — unvalidated

After applicable simulation tests and the [hardware prerequisites](hardware.md), a serial definition could use `connection_url = "serial:///dev/serial/by-id/<device>:57600"`, with the actual device path substituted, and the reviewed target ID. Ensure host permissions and baud rate match the physical link. For a network telemetry bridge, use its actual UDP/TCP destination and route MAVLink to the configured listener.

Confirm the correct ArduPilot logical serial port and its `SERIALx_PROTOCOL` (1 for MAVLink1 or 2 for MAVLink2) and `SERIALx_BAUD` settings using the [official telemetry port guide](https://ardupilot.org/copter/docs/common-telemetry-port-setup.html). Confirm `SYSID_THISMAV` independently. MAMBA does not change firmware parameters. No physical connection, firmware compatibility, or hardware readiness is claimed by this example.

## Validation evidence

Automated coverage: `uv run --locked pytest -q`. On 2026-10-26, after `uv sync --locked`, `.venv/bin/python -m pytest -q` reported 28 passed in 18.81s on Linux/Python 3.14.4 (FastMCP 2.14.7, MAVSDK 4.0.6). Two upstream Authlib deprecation warnings were emitted; protocol checks passed. Unit tests use a controlled MAVSDK substitute for matching, nonmatching and duplicate IDs, discovery timeout, transport/SDK failures, disconnect, recovery, persistence, and cleanup. Stdio tests exercise tool discovery, status, `ping`, absent/invalid/missing configuration, and real native MAVSDK on an empty loopback UDP endpoint. The latter verifies timeout and protocol isolation, not successful vehicle discovery.

ArduPilot SITL and physical acceptance remain pending; no running SITL container was available during implementation. Feature F2 is partially implemented and is not marked accepted.
