# Vehicle information and telemetry — MAMBA-26 / MAMBA-27

This implements vehicle information retrieval (MAMBA-26, under F2 — MAVSDK Drone Connection) and the read-only telemetry part of F3 — Basic Tools (MAMBA-27). ArduPilot SITL and hardware acceptance remain pending. Navigation, state machines, authorization, and multi-vehicle routing remain planned.

## Startup and catalog

Use the existing [connection configuration](connection.md):

```bash
uv run --locked python src/mamba/server.py --config config/vehicle.example.toml
```

The catalog contains four tools. Call `get_vehicle_status` and wait for `connected` before retrieving vehicle data. Tools use only the configured autopilot; callers cannot select a different ID or endpoint.

| Tool | Arguments | Result |
| --- | --- | --- |
| `ping` | `{}` | `pong` |
| `get_vehicle_status` | `{}` | Existing connection status |
| `get_vehicle_information` | `{}` | Identification and software versions, with partial errors |
| `get_vehicle_telemetry` | Required `fields` array | Selected readings and per-category errors |

The three vehicle-read tools have read-only annotations. Request telemetry explicitly, for example `{"fields":["position","battery","health"]}`. Valid categories are `position`, `velocity`, `battery`, `gps`, and `health`. Lists must contain 1–5 unique categories. Empty lists, duplicate/unknown names, or omitted fields are rejected before accessing MAVSDK. There is no retrieve-everything default.

## Results and migration

The five previous tools (`get_vehicle_position`, `get_vehicle_velocity`, `get_vehicle_battery`, `get_vehicle_gps`, and `get_vehicle_health`) have been removed from MCP discovery and invocation. Migrate each call to `get_vehicle_telemetry` with the corresponding category in `fields`; multiple categories can be requested together. Internal retrieval methods remain separate. `ping`, status, and information interfaces are unchanged.

Telemetry results contain `system_id`, typed `readings`, and `errors`. Each successful requested category has its own UTC ISO 8601 `received_at` and typed `data`. Only successful requested categories appear in `readings`; only failed requested categories appear in `errors`. For example:

```json
{
  "system_id": 1,
  "readings": {
    "position": {
      "received_at": "2026-11-03T12:00:00+00:00",
      "data": {
        "latitude_deg": 40.0,
        "longitude_deg": -74.0,
        "absolute_altitude_m": 125.5,
        "relative_altitude_m": 0.0
      }
    }
  },
  "errors": {"battery": "timeout: no battery reading within 10s"}
}
```

This is an illustrative partial result for `fields=["position","battery"]`. Categories are independently observed and are not a simultaneous snapshot.

| Category | Data fields and units |
| --- | --- |
| `position` | `latitude_deg`, `longitude_deg`, `absolute_altitude_m` (AMSL), `relative_altitude_m` (SDK relative altitude) |
| `velocity` | `north_m_s`, `east_m_s`, `down_m_s` (positive down, NED frame) |
| `battery` | `id`, `temperature_degc`, `voltage_v`, `current_battery_a`, `capacity_consumed_ah`, `remaining_percent` (0–100), `time_remaining_s`, `battery_function` |
| `gps` | `num_satellites`, `fix_type` |
| `health` | `is_gyrometer_calibration_ok`, `is_accelerometer_calibration_ok`, `is_magnetometer_calibration_ok`, `is_local_position_ok`, `is_global_position_ok`, `is_home_position_ok`, `is_armable` |

Enums retain SDK names such as `NO_FIX` or `RELEASE`. Unknown/non-finite numeric measurements remain JSON `null` inside successful readings. Zero values and false health flags remain valid data. Battery retrieval returns one update including its battery ID, not an aggregate of every battery.

Information results retain `system_id`, `received_at`, and `data` containing `identification`, `version`, and `errors`. Identification includes hardware/legacy UIDs; versions include flight/vendor/OS major/minor/patch values, flight/OS Git hashes, and release type. Both sections are requested concurrently. An unavailable section is null with an explicit error; if neither succeeds, the call is a tool error.

## Deadlines, errors, and cleanup

`vehicle_data.py` owns retrieval and response models, `server.py` registers tools, and `connection.py` owns the persistent transport and generation. Requested telemetry categories start concurrently under one shared 10-second acquisition deadline. Each subscribes on demand for one SDK callback and closes its subscription/plugin after success, failure, timeout, or cancellation. Pending requests are cancelled at the deadline and cleanup completes before returning. Caller cancellation and service shutdown drain all child requests.

There is no application telemetry cache or explicit stream-rate change. A silent topic can time out while other requested categories succeed. Partial successes return readings plus errors; no successful categories produces `telemetry_unavailable` as an MCP tool error. Position/velocity may not be published without a usable position estimate.

The configured target and connection generation are validated before dispatch and before returning. A detected disconnect/reconnect, invalid target, or inconsistent connection invalidates the entire batch, including earlier successes. Other error prefixes include `not_connected`, `invalid_target`, `connection_changed`, `timeout`, `missing_reading`, `sdk_error`, and `information_unavailable`. The MCP server and `ping` remain available.

Information operations still run in an executor and cannot safely be stopped on caller timeout/cancellation. Pending work is shared within one connection generation and drained before plugin/SDK destruction. Shutdown can therefore exceed a caller deadline while native work finishes. Diagnostic logs record target, operation, outcome/reason, and elapsed milliseconds; the F4 audit trail remains planned.

## Timestamp and safety limits

`received_at` records MAMBA receipt of an SDK result, not its sensor measurement time or validated source age. The SDK may supply stored state. See [MAVSDK data handling](https://mavsdk.mavlink.io/main/en/cpp/guide/general_usage.html). Different category timestamps must remain visible. Health/armability flags and connection status do not authorize actions or satisfy future safety-state freshness requirements.

## Validation and pending SITL acceptance

`uv run --locked pytest -q` passed **76 tests in 18.64s** on 2026-11-03, with two upstream Authlib deprecation warnings. Tests cover retrieval methods, selective concurrent batches, invalid selections, partial/total failure, a shared deadline, cancellation/shutdown cleanup, whole-batch reconnect rejection, four-tool discovery, typed MCP serialization, removed tool names, and continued responsiveness. Native SDK integration covers empty-endpoint startup/timeout only.

Before claiming ArduPilot acceptance, follow the [connection runbook](connection.md), then compare information and all five categories against independent SITL/GCS observations. Exercise missing GPS/unsupported information, silent topics, partial/total failures, disconnect during a batch, recovery, and cleanup. Record versions, IDs, endpoints, timestamps, values, reasons, and elapsed times. No new SITL or hardware acceptance run was performed for this consolidation.

See the [interface size comparison](../../benchmarks/telemetry-interface.md): fewer descriptors are exposed, while representative response payloads grow slightly. Byte measurements do not establish model token savings, agent reliability, or flight readiness.
