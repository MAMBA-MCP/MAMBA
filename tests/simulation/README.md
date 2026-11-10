# ArduPilot SITL → MAMBA → Codex acceptance test

This manual test checks MCP responsiveness (F1/A01), MAVSDK Drone Connection
(MAMBA-2 / F2/A02), vehicle information (MAMBA-26), and read-only telemetry
(MAMBA-27, part of F3 — Basic Tools). It uses a stationary ArduCopter SITL
vehicle and the Codex CLI or IDE extension as the MCP harness. No arming or
flight commands are required or exposed by MAMBA.

The procedure is not an automated runner. A successful four-tool smoke check
was observed on November 9, 2026; the full acceptance sequence below, including
disconnect/recovery and independent value comparisons, remains pending.

## 1. Prepare ArduPilot and MAMBA

Use Linux/Ubuntu with a working compiler/build environment, Python 3.11+, uv,
Git, and Codex. Install ArduPilot separately from this repository using its
[Linux build environment instructions](https://ardupilot.org/dev/docs/building-setup-linux.html)
and [SITL setup guide](https://ardupilot.org/dev/docs/setting-up-sitl-on-linux.html).
Those instructions cover cloning ArduPilot with submodules, installing its
prerequisites, and updating the shell environment. Record the chosen ArduPilot
revision; using a changing development branch makes runs harder to reproduce.

From the MAMBA repository root:

```bash
uv sync --locked
uv run --locked pytest -q
```

Keep the pytest result with the run evidence. Automated tests do not replace
the live SITL checks below.

## 2. Start a stationary SITL vehicle

From the root of your separate ArduPilot checkout:

```bash
./Tools/autotest/sim_vehicle.py -v ArduCopter --console --map
```

The first launch builds SITL and starts MAVProxy. On a headless host omit
`--console --map` and use the terminal MAVProxy prompt. For a fresh, disposable
simulation, the optional `-w` argument resets simulated EEPROM parameters;
do not add it when preserving an existing simulation configuration.

At the **MAVProxy prompt**, check the autopilot ID and add an output:

```text
param show SYSID_THISMAV
output add 127.0.0.1:14540
output
```

Use system ID `1` for this procedure. If the parameter differs, either use
that ID in MAMBA's configuration or deliberately change the simulated vehicle
parameter and restart SITL as needed. Record the actual ID.

The loopback destination above applies when MAVProxy and MAMBA share a network
namespace. Across a container, VM, WSL boundary, or remote host, replace
`127.0.0.1` with an address reachable from MAVProxy that belongs to the MAMBA
host. Record that destination and any UDP port forwarding. An entry in
`output` confirms routing configuration, not successful packet delivery.

See the official [SITL usage guide](https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html)
for launch options and alternate ground-station arrangements.

## 3. Configure the MAMBA UDP listener

Edit `config/vehicle.example.toml`, or create a machine-local TOML file:

```toml
[vehicle]
connection_url = "udpin://0.0.0.0:14540"
system_id = 1
```

`0.0.0.0` binds the receiver to all local IPv4 interfaces. `127.0.0.1` restricts
it to loopback. Use a specific local interface address when appropriate for
your network. `0.0.0.0` is a bind address, not MAVProxy's destination, and does
not by itself route packets across network namespaces or open a firewall.

In the observed smoke check, changing the listener from `127.0.0.1` to
`0.0.0.0` and restarting the server allowed discovery. The precise packet path
was not captured, so this does not establish which interface carried traffic.

## 4. Connect the Codex MCP harness

Use absolute paths to the repository and uv executable, substituting your
actual paths for every `/absolute/path` placeholder:

```bash
codex mcp add mamba -- /absolute/path/to/uv run --locked --project /absolute/path/to/MAMBA python /absolute/path/to/MAMBA/src/mamba/server.py --config /absolute/path/to/MAMBA/config/vehicle.example.toml
codex mcp list
codex mcp get mamba
```

If `mamba` is already registered, inspect and update its existing entry rather
than adding a second server. The equivalent entry in `~/.codex/config.toml` is:

```toml
[mcp_servers.mamba]
command = "/absolute/path/to/uv"
args = ["run", "--locked", "--project", "/absolute/path/to/MAMBA", "python", "/absolute/path/to/MAMBA/src/mamba/server.py", "--config", "/absolute/path/to/MAMBA/config/vehicle.example.toml"]
cwd = "/absolute/path/to/MAMBA"
```

Codex starts and owns the stdio subprocess; MAMBA has no HTTP URL. Avoid a
second manually launched listener on the same UDP port. Configuration is read
once at startup. After editing it, exit and reopen Codex CLI, or reload the
IDE extension host (in VS Code, Command Palette → `Developer: Reload Window`).
Verify the new session discovers exactly the four tools below. See the
[official Codex MCP documentation](https://developers.openai.com/codex/mcp).

## 5. Check all four tools through the harness

Ask Codex:

> Use only MAMBA to call ping and get_vehicle_status. Report the complete
> results. Wait for system ID 1 to be connected before requesting vehicle data.

Then, once connected:

> Use MAMBA to call get_vehicle_information with no arguments, and
> get_vehicle_telemetry with fields ["position", "velocity", "battery", "gps",
> "health"]. Show the structured results, timestamps, and errors.

Inspect actual tool-call arguments/results in the harness transcript; a prose
answer alone is insufficient evidence.

| Tool | Arguments | Pass criteria |
| --- | --- | --- |
| `ping` | `{}` | Returns `pong`, without a tool error. |
| `get_vehicle_status` | `{}` | `state` is `connected`, `system_id` is `1`, and `discovered_system_ids` contains `1`; observation timestamps are present. |
| `get_vehicle_information` | `{}` | Correct `system_id`, receipt timestamp, identification and version data; compare firmware version with the SITL startup banner. Record missing/unsupported sections explicitly. |
| `get_vehicle_telemetry` | `{"fields":["position","velocity","battery","gps","health"]}` | All five readings have data and individual receipt timestamps, with an empty `errors` object for this nominal scenario. |

Compare telemetry with MAVProxy/GCS observations from the same run: map
coordinates, relative altitude near the ground, approximately zero stationary
NED velocity, battery values, GPS fix/satellite count, and reported health.
Capture the independent observations and define comparison tolerances before
grading the run. Values depend on the simulator configuration; do not require
a particular coordinate, GPS fix type, or `is_armable=true` as a universal
expected value. Explain any discrepancy before marking a check passed.

Repeat status and telemetry at least three times without restarting MAMBA to
check persistence. Record elapsed times. Telemetry uses a shared 10-second
acquisition deadline; a partial response is valid API behavior but does not
pass this nominal all-category check. Receipt time is not sensor measurement
time or proof of freshness. Health flags do not authorize vehicle actions.

## 6. Check disconnect and recovery

1. Stop SITL/MAVProxy using Ctrl+C. Leave the Codex session and MAMBA running.
2. Query status until it reports `disconnected`. Record time from stopping
   SITL to detection; polling is one second, plus MAVSDK heartbeat-loss delay.
3. Call `ping`: it must still return `pong`. Once status reports the loss,
   information and telemetry must fail with `not_connected` rather than return
   vehicle data as if the vehicle were available.
4. Restart SITL with the same ID and restore the MAVProxy output. Status must
   return to `connected` without restarting MAMBA. Repeat all four tool checks.
5. Stop the harness-managed MCP process and simulator at completion. Remove
   temporary routing/configuration only if created for this run, and record
   whether shutdown left any listener or simulator processes behind.

Initial discovery takes up to a 10-second window followed by five-second
retries. A never-seen target can report `error`; after an observed connection,
loss reports `disconnected`. Both may alternate with `connecting` on retries.

## Troubleshooting

| Observation | Checks |
| --- | --- |
| `ping` fails or tools are absent | Inspect Codex MCP startup logs, absolute executable/config paths, dependencies, and stdio protocol errors. |
| `unconfigured` | Ensure the harness launch arguments include `--config` and its absolute path. |
| Empty discovered IDs | Verify actual UDP traffic at the MAMBA host, matching port, bind interface, routing, firewall, and container/VM boundaries. A MAVProxy output entry alone does not prove receipt. |
| Other discovered IDs | Compare `SYSID_THISMAV` with the configured target; MAMBA intentionally refuses to substitute another autopilot. |
| Configuration changed but behavior did not | Restart the harness-managed subprocess and verify the exact config path. |
| Connected but data missing | Save per-section/category errors; check SITL topic publication and SDK compatibility. Do not silently grade partial data as a full pass. |

When available, `ss -lunp` on the MAMBA host identifies UDP listeners, and
`sudo tcpdump -ni any udp port 14540` shows packet arrival. Run these in the
server's network namespace; a restricted agent shell may expose a different
process/network view. Avoid starting a competing UDP receiver for diagnosis.

## Evidence and acceptance record

Create a run record containing:

- Operator, UTC start/end times, OS and host/container/VM topology.
- MAMBA Git revision, Python/uv/Codex versions, locked MAVSDK/FastMCP versions,
  ArduPilot revision/firmware and MAVProxy version.
- Exact launch commands, configuration path/content, output destination,
  listener address, expected/discovered IDs, and restart method.
- Raw MCP arguments/results, errors, elapsed times, independent GCS readings,
  comparison tolerances, and disconnect/recovery timestamps.
- Pass/fail/not-run for each step, limitations, and links to saved evidence.

Observed smoke-check evidence from this session (November 9, 2026,
`2026-11-10T02:40:50Z`): all four tools succeeded for system `1`, firmware
`4.8.0 DEV`; all five telemetry categories returned with no errors. The run
reported position `-35.3632622, 149.1652375`, battery approximately `12.6 V` /
`100%`, ten satellites, and `RTK_FIXED`. These are sample observations, not
fixed test expectations. Independent comparisons, reproducible installation,
disconnect/recovery, unsupported/silent topics, cancellation, identity
isolation, and cleanup were not established by that smoke check. Full F2/F3
acceptance and hardware acceptance remain pending.

Map completed evidence into the [acceptance matrix](../../docs/testing/acceptance-matrix.md).
See the [connection runbook](../../docs/runbooks/connection.md) and
[vehicle-data runbook](../../docs/runbooks/vehicle-data.md) for detailed API
behavior and additional failure scenarios.
