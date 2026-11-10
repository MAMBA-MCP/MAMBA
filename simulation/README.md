# Validate MAMBA with ArduCopter SITL

This guide covers all four MAMBA MCP tools. Use the manual walkthrough to check your own simulator connection, then run the automated acceptance harness to compare results against MAVLink frames and test failure recovery. Keep the simulated vehicle disarmed for both checks.

## 1. Set up ArduPilot and MAMBA

Use Ubuntu 24.04 or the same Ubuntu 24.04 WSL2 distribution for SITL, MAVProxy, and the MAMBA subprocess. Install Git, Python 3.11+, and [uv](https://docs.astral.sh/uv/getting-started/installation/). The examples use `~/ardupilot` and `~/projects/MAMBA`. Reuse existing checkouts and adjust paths to match your machine.

For a new ArduPilot checkout, run the Ubuntu prerequisite installer and reload your shell environment. See the [ArduPilot Ubuntu setup guide](https://ardupilot.org/dev/docs/building-setup-linux.html).

```bash
git clone --recurse-submodules https://github.com/ArduPilot/ardupilot.git ~/ardupilot
cd ~/ardupilot
Tools/environment_install/install-prereqs-ubuntu.sh -y
. ~/.profile
./waf configure --board sitl
./waf copter
```

The build should produce `~/ardupilot/build/sitl/bin/arducopter`. MAVProxy must also be available on the WSL shell’s `PATH` for the manual walkthrough. For a new MAMBA checkout, clone the repository and install its locked dependencies.

```bash
mkdir -p ~/projects
git clone https://github.com/MAMBA-MCP/MAMBA.git ~/projects/MAMBA
cd ~/projects/MAMBA
uv sync --locked --group simulation
```

If uv lives in a local tooling environment, use its absolute path in place of `uv`. The existing WSL setup uses `~/projects/MAMBA/.tools/bin/uv`. If an ArduPilot virtual environment is active, run the MAMBA commands in a separate shell or prefix them with `env -u VIRTUAL_ENV`.

## 2. Start SITL and route MAVLink

In a WSL terminal, start a quadrotor with MAVProxy. Use an existing SITL session if one is already running. See the [ArduPilot SITL guide](https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html).

```bash
cd ~/ardupilot/ArduCopter
../Tools/autotest/sim_vehicle.py -v ArduCopter -f quad
```

At the **MAVProxy prompt**, run `output` and check for `127.0.0.1:14540`. If it’s missing, add the destination and check again.

```text
output add 127.0.0.1:14540
output
```

MAVProxy can keep its existing ground station outputs. A Windows host destination on port `14550` serves a different endpoint from `127.0.0.1:14540` inside WSL. Check the simulated system ID with `param show MAV_SYSID` in MAVProxy. Older firmware uses `SYSID_THISMAV`.

## 3. Connect the MCP client

The [example TOML](../config/vehicle.example.toml) listens on WSL loopback UDP port `14540` for system ID `1`. If your simulator uses a different ID or port, copy the TOML and adjust the values and the MAVProxy destination together.

Configure your MCP client to launch the server over stdio. In a WSL-based client, use this command and expand `~` to an absolute path in the client configuration.

```bash
~/projects/MAMBA/.venv/bin/python ~/projects/MAMBA/src/mamba/server.py \
  --config ~/projects/MAMBA/config/vehicle.example.toml
```

For Windows Codex, use the following PowerShell registration command if `MAMBA` is absent from `codex mcp list`. Replace `/home/jank` and the distribution name with your own values. After registering or updating the entry, reload MCP servers in Codex and check that the four tools appear in the session.

```powershell
codex mcp add MAMBA -- C:\Windows\System32\wsl.exe -d Ubuntu-24.04 --exec /home/jank/projects/MAMBA/.venv/bin/python /home/jank/projects/MAMBA/src/mamba/server.py --config /home/jank/projects/MAMBA/config/vehicle.example.toml
```

The client owns the server process. Close any standalone MAMBA process already listening on `14540` before starting the client-managed instance. See the [connection runbook](../docs/runbooks/connection.md) for server settings and discovery behavior.

## 4. Call and validate every tool

Call the tools in this order. Wait for `connected` before requesting information or telemetry, and let the simulator’s GPS and estimator settle before assessing position and health.

| Tool | Arguments | Passing result |
| --- | --- | --- |
| `ping` | `{}` | `pong` confirms the MCP process responds. |
| `get_vehicle_status` | `{}` | `state` is `connected`. `system_id` matches the configured ID, and `discovered_system_ids` includes it. |
| `get_vehicle_information` | `{}` | Identification and flight software version are present, with an empty `data.errors`. Compare the version numbers with the ArduCopter startup banner. |
| `get_vehicle_telemetry` | `{"fields":["position","velocity","battery","gps","health"]}` | `system_id` matches the target, all five categories appear in `readings`, and `errors` is empty. |

Compare latitude and longitude to the simulator location, absolute altitude to the simulated altitude above mean sea level, and relative altitude to the home reference. A stationary, disarmed quad should show near-zero NED velocity. Positive down velocity indicates descent. Check that battery voltage and charge are plausible for the simulator, and confirm a GPS fix and satellite count. Inspect the health flags after estimator initialization. Optional battery fields can be `null`, and `is_armable` describes armability. Receipt times record when MAMBA got each reading. The automated harness below provides the independent wire comparison and exact tolerances.

Call telemetry again with `{"fields":["battery"]}` and confirm `readings` contains only `battery`. A request with `{"fields":[]}` should return a validation error. Repeat `ping` afterward and expect `pong`.

To check reconnect behavior, temporarily remove the test route using `output remove 127.0.0.1:14540` in MAVProxy. If MAVProxy lists the route with a prefix, use its listed index with `output remove <index>`. Poll status until the link loss is reported, and confirm `ping` still returns `pong`. Add the route again and verify that the same MCP process returns to `connected` and serves telemetry. Heartbeat timeout and discovery retries can take several seconds.

## 5. Run automated acceptance

Run this from the MAMBA checkout. Choose a fresh output path for each run. The harness uses SITL instance `31` and dynamically selected loopback ports, starts its own simulator, and cleans up its processes on exit. Leave instance `31` available.

```bash
cd ~/projects/MAMBA
uv run --locked --group simulation python tests/simulation/validate_read_only.py \
  --ardupilot "$HOME/ardupilot" --output /tmp/mamba-sitl-acceptance
```

A passing run exits with code `0` and reports `"passed": true`. Check the output directory for `report.json`, `wire-observations.jsonl`, `sitl.log`, and `mcp-*.log`. The harness checks all four MCP tools, compares readings with independent MAVLink observations, and exercises partial and total failures, request cancellation, disconnect, and recovery. See the [acceptance record and tolerances](../docs/testing/mamba-26-27-sitl.md).

To run the standard unit and integration suite separately, use `uv run --locked pytest -q`. The [MAVLink-M compatibility scenario](../docs/runbooks/mavlink-m.md) covers custom XML and `PARTICIPANT_POSITION` separately from the four MCP tools.

## Troubleshooting and cleanup

| Symptom | Check |
| --- | --- |
| Tools are missing | Verify the client registration, WSL distribution, Python executable, and absolute paths. Reload the MCP server and inspect startup diagnostics. |
| `ping` works and status is `unconfigured` | Add `--config` with the absolute TOML path to the client command and restart the server. |
| Status remains `connecting` or reports a discovery timeout | Confirm the SITL heartbeat reaches MAVProxy, the route includes `127.0.0.1:14540`, and the configured system ID matches. |
| Port is already in use | Run `ss -lunp` in WSL to find the listener. Close the duplicate MAMBA process or choose a free port and update both endpoints. |
| Connected but a telemetry category times out | Confirm MAVProxy is forwarding telemetry streams and allow the estimator to initialize. Inspect the category error and compare with the simulator’s telemetry. |
| Firmware Git hash looks unexpected | MAMBA passes through SDK-derived version fields. Compare flight version numbers and consult the [known formatting issue](../docs/testing/mamba-26-27-sitl.md#limits-and-open-observations). |

After the manual check, remove any MAVProxy output you added solely for the test. Stop SITL with Ctrl+C in its terminal if you started it for this walkthrough. Keep the acceptance report and logs with the MAMBA commit and ArduPilot revision used for the run.
