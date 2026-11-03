# Vehicle information and telemetry — MAMBA-26 / MAMBA-27

This implements vehicle information retrieval (MAMBA-26, under F2 — MAVSDK Drone Connection) and the read-only telemetry part of F3 — Basic Tools (MAMBA-27). ArduPilot SITL and hardware acceptance remain pending. Navigation, state machines, authorization, and multi-vehicle routing remain planned.

## Startup and tools

Use the existing [connection configuration](connection.md). Start the MCP server with a TOML file selecting the expected system ID:

```bash
uv run --locked python src/mamba/server.py --config config/vehicle.example.toml
```

Connect an MCP client, call `get_vehicle_status` with `{}`, and wait for `connected`. The six tools below also take `{}` and are annotated as read-only. They use only the configured connected autopilot; callers cannot select a different ID or endpoint. `ping` and `get_vehicle_status` retain their existing interfaces.

| Tool | `data` fields and units |
| --- | --- |
| `get_vehicle_information` | `identification`: `hardware_uid`, `legacy_uid`; `version`: flight/vendor/OS software major/minor/patch values, flight/OS Git hashes, flight release type; `errors`: unavailable sections and reasons |
| `get_vehicle_position` | `latitude_deg`, `longitude_deg`, `absolute_altitude_m` (AMSL), `relative_altitude_m` (SDK relative altitude) |
| `get_vehicle_velocity` | `north_m_s`, `east_m_s`, `down_m_s` (positive down, NED frame) |
| `get_vehicle_battery` | `id`, `temperature_degc`, `voltage_v`, `current_battery_a`, `capacity_consumed_ah`, `remaining_percent` (0–100), `time_remaining_s`, `battery_function` |
| `get_vehicle_gps` | `num_satellites`, `fix_type` |
| `get_vehicle_health` | `is_gyrometer_calibration_ok`, `is_accelerometer_calibration_ok`, `is_magnetometer_calibration_ok`, `is_local_position_ok`, `is_global_position_ok`, `is_home_position_ok`, `is_armable` |

Every successful result has the typed envelope `system_id`, `received_at` (UTC ISO 8601), and `data`. Enum values use SDK names such as `NO_FIX` or `RELEASE`. Unknown/non-finite numeric values become JSON `null`; zero values and false health flags remain valid values. Battery retrieval returns the first battery update observed during the request, including its ID; it does not aggregate multiple batteries.

The information tool requests identification and version concurrently. If only one section succeeds, the other section is `null` and its reason appears under `data.errors`. If neither succeeds, the tool returns an MCP tool error.

## Retrieval and failure behavior

`src/mamba/vehicle_data.py` owns SDK retrieval and response models. `server.py` registers tools; `connection.py` owns the persistent transport and connection generation. Retrieval uses the existing native `InfoAsync` and `TelemetryAsync` APIs, with no dependency changes.

Each telemetry call subscribes on demand, waits for one SDK callback, and closes its subscription and plugin on success, failure, timeout, or cancellation. MAMBA does not retain telemetry results across calls or explicitly change stream rates. Calls have a fixed 10-second deadline. A silent topic times out independently; position/velocity may not be published without a usable position estimate. False health flags and a missing GPS fix are returned as data, not treated as transport errors.

Before and after retrieving data, MAMBA checks the configured ID, SDK connectivity, autopilot presence, and connection generation. A detected disconnect/reconnect invalidates pending results, even if the same ID reconnects. Target mismatch or an unavailable/error connection also prevents data from being returned as a successful current reading.

Errors use MCP tool errors with a reason prefix: `not_connected`, `invalid_target`, `connection_changed`, `timeout`, `missing_reading`, `sdk_error`, or `information_unavailable`. The server and its `ping` tool remain available. Request logs include target ID, operation, outcome/reason, and elapsed milliseconds; these are diagnostic logs, not implementation of the proposed F4 audit trail.

Native information requests run in an executor and cannot safely be stopped when the MCP caller times out or cancels. MAMBA tracks them, shares still-running requests within the same connection generation, and destroys their plugin only after both native requests finish. Shutdown cancels active tool readers and waits for outstanding native operations before destroying the connection SDK. Shutdown can therefore outlast the caller's 10-second deadline if native code is still running.

## Timestamp and safety limits

`received_at` records when MAMBA received the SDK result. It is not a sensor measurement timestamp and does not establish source freshness. The SDK may supply its latest stored state; MAMBA cannot infer its true source age from these topics. See [MAVSDK data handling](https://mavsdk.mavlink.io/main/en/cpp/guide/general_usage.html) and the [native Python API](https://mavsdk.mavlink.io/v4/en/python/migration.html). These tools provide observations; health/armability flags and connection status do not authorize vehicle actions or satisfy future safety-state freshness requirements.

## Validation and SITL acceptance

Run `uv run --locked pytest -q` and `git diff --check`. Controlled substitutes cover all six successful reads, units/serialization, missing values, partial information, timeouts, SDK failures, cancellation, concurrent requests, disconnect/reconnect rejection, native-work sharing, and cleanup. MCP tests exercise tool schemas, typed results, read-only annotations, controlled errors, and continued responsiveness. Real SDK empty-endpoint tests validate startup and timeout only.

When an ArduPilot SITL instance is available, follow the [connection runbook](connection.md), then:

1. Confirm the configured ID is connected and call all six tools, recording actual values and elapsed time. Compare position, NED velocity, battery, GPS, health, identification, and version with independent SITL/GCS observations.
2. Exercise missing GPS/unsupported information and silent topics; retain the actual partial results or timeout reasons. Do not invent values for unavailable fields.
3. Interrupt the link during a read; verify controlled failure and continued `ping` responsiveness. Reconnect the same ID and verify later requests succeed without reusing an earlier session's result.
4. Stop the MCP client/server and SITL; retain firmware/SDK versions, endpoint/IDs, timestamps, output, and cleanup evidence.

SITL validation is pending until these steps are executed and recorded. Read-only test coverage does not establish acceptance for F3 navigation commands or hardware readiness.

Automated evidence on 2026-11-03: `uv run --locked pytest -q` passed **58 tests in 18.65s** with two upstream Authlib deprecation warnings; `git diff --check` passed. No SITL executable or running container was available. See the [development record](../development.md) for environment and sandbox details.
