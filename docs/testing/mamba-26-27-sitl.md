# MAMBA-26/27 read-only SITL acceptance

Validated on 2026-11-03 in Ubuntu 24.04 / WSL2 using Python 3.12.3,
FastMCP 2.14.7, native MAVSDK 4.0.6, MCP 1.30.0 and pymavlink 2.4.49.
The baseline was MAMBA `e7bb91ef2f02b590e37c50d5397cf693c0f80e97`.
ArduPilot source checkout: `9165d22419406556fc9815d9f4e3e299e13713a8`;
the simulated vehicle reports ArduCopter 4.8.0 DEV. The source revision alone
does not prove the provenance of an existing build; the exact executable and
default parameter file SHA-256 values are retained in the evidence.

## Reproduce in WSL

Prerequisite: a built ArduPilot checkout with `build/sitl/bin/arducopter` and
`Tools/autotest/default_params/copter.parm`. This scenario uses the native quad
physics model and does not require Gazebo, MAVProxy or a graphical GCS.
For installation/build prerequisites see the official
[ArduPilot SITL guide](https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html).

From the MAMBA root:

```bash
uv sync --locked --group simulation
uv run --locked --group simulation python tests/simulation/validate_read_only.py \
  --ardupilot "$HOME/ardupilot" --output /tmp/mamba-read-only-acceptance
```

Use a **new output directory** for every run. The script launches only the
specified simulator, uses isolated EEPROM/logs in that directory, system ID 1,
instance 31, home 40 degrees N / 74 degrees W / 125 m AMSL, and dynamically
allocated loopback UDP endpoints. Ensure instance 31 is unused. Two short-lived
UDP port reservations have a small release/rebind race; a collision must be
resolved by rerunning, not accepted as a passing scenario.

A local router requests MAVLink telemetry streams at 4 Hz, as a GCS normally
would. Bare SITL did not publish the required topics without this setup.
It decodes simulator frames independently with pymavlink, forwards them to
MAMBA, and forwards SDK traffic back. Faults drop selected frames or black out
the link; they do not alter physical devices. The script never arms or moves
the simulator or writes vehicle parameters. Each fault starts a fresh MCP/SDK
session where necessary so retained SDK data cannot mask missing topics.

The command fails on an assertion, timeout or process error. It writes
`report.json` even on failure, plus `mcp-*.log`, `sitl.log` and
`wire-observations.jsonl`. MCP session contexts close their subprocesses and
the simulator is terminated in `finally`, with a bounded kill fallback.

## Results

The final run passed from `2026-11-03T19:03:18.740538+00:00` to
`2026-11-03T19:04:29.914092+00:00`. The full machine-readable record is
[evidence/mamba-26-27-wsl.json](evidence/mamba-26-27-wsl.json).
Raw diagnostic/wire files from this local run remain in `/tmp/mamba-sitl-final`;
temporary files are not permanent storage. The retained JSON contains actual
MCP responses and the independent frames used for comparisons.

| Scenario | Result |
| --- | --- |
| Discover and retain configured target | Connected as system ID 1; repeated calls retained connection |
| MAMBA-26 identification/version | Hardware UID, legacy UID and flight major/minor/patch matched `AUTOPILOT_VERSION` |
| MAMBA-27 position | Latitude/longitude and absolute/relative altitude matched `GLOBAL_POSITION_INT` |
| NED velocity | All three components matched `GLOBAL_POSITION_INT`, converting cm/s to m/s |
| Battery | Voltage and remaining percentage matched `SYS_STATUS`; unsupported measurements remained null |
| GPS | Satellite count and fix type matched `GPS_RAW_INT` |
| Health | Typed flags returned; local/global/home flags became true; independent heartbeat remained disarmed |
| Selective fields | Battery-only request returned only battery |
| Missing position | Battery returned with explicit position timeout in 10.082 s |
| Missing position and velocity | Controlled `telemetry_unavailable` in 10.011 s under one deadline |
| Request cancellation | Pending position call cancelled; subsequent battery call succeeded in the same session |
| Link loss during batch | Whole batch rejected with `connection_changed`; disconnect observed after 2.582 s |
| Disconnected MCP | `ping` returned `pong`; information returned `not_connected` |
| Restore link | Same MCP process recovered and returned all five categories |
| Missing information messages | Filtering `AUTOPILOT_VERSION` produced explicit `information_unavailable` |
| Missing GPS messages | Battery returned with explicit GPS timeout |
| Shutdown | All stdio contexts exited; simulator exited with code 0 |

Comparison tolerances are explicit in the harness and retained JSON:
coordinates 1e-5 degrees, altitude 0.5 m, velocity 0.15 m/s, voltage 0.1 V,
remaining charge 1 percentage point, and satellite count exact. Independent
reference messages must be within 3 seconds of the category receipt time.
These tolerances are acceptance-test choices, not vehicle operating limits.

## Limits and open observations

- The simulator remained stationary and disarmed. Dynamic flight, nonzero
  velocity sign behavior, other frames/firmware, hardware, multiple vehicles,
  safety freshness, authorization and MAVLink-M remain outside this evidence.
- Health flags were observed and readiness checked, but individual calibration,
  estimator and armability failure semantics were not independently fault-tested.
  Armable does not mean armed or authorized to act.
- Faults suppress wire messages; missing GPS data is not a simulated loss of GPS
  fix. Partial identification/version failures and explicit `NO_FIX`/false-health
  serialization remain covered by the existing controlled tests.
- SDK-provided version strings are passed through. In the first complete run,
  raw ArduPilot `flight_custom_version` bytes decoded as `9165d224`, while MAVSDK
  returned `flight_sw_git_hash="343232643"`. Vendor version fields also reflect
  SDK interpretation of those bytes. Do not treat these fields as a normalized
  ArduPilot Git revision. Resolving that SDK mapping is separate follow-up work;
  this scenario validates flight version numbers, not those derived fields.
- Sensor timestamps/freshness are not established by receipt timestamps. No
  production retrieval changes were required for the exercised scenarios.
  Broader F2/F3, simulator-pipeline and hardware acceptance remain open.
