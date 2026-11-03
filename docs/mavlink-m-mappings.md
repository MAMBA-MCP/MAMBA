# Message support and mapping gaps — MAMBA-30

Scope: Dronecode/mavlink-military revision
`23cec36751681aa281c1e5ca6b222a07c6c0c002`, native MAVSDK 4.0.6, and the
MAMBA-28/29 isolated experiment. The complete XML loader accepted all definitions;
only the own-position report has independent wire evidence. Loading a definition
does not create a typed SDK capability, implement vehicle behavior, or add an
MCP tool. There is no generic message-sending MCP tool.

## Existing standard information/telemetry

| MAMBA capability | SDK / observed wire basis | Mapping limits |
| --- | --- | --- |
| Identification and version | Info / `AUTOPILOT_VERSION` | SDK-derived Git hash/vendor fields differ from raw ArduPilot custom version bytes; normalization remains open |
| Position and NED velocity | Telemetry / `GLOBAL_POSITION_INT` | Convert degE7, mm and cm/s; receipt time does not establish source age |
| Battery | Telemetry / observed `SYS_STATUS` | Voltage and charge validated; unsupported measurements remain null; no multi-battery aggregation |
| GPS | Telemetry / `GPS_RAW_INT` | Fix name and satellite count validated; no automatic no-fix-to-usable-position inference |
| Health | Telemetry / SDK-composed flags | No one-to-one custom-message mapping; per-flag failure semantics not independently accepted |

## Pinned custom-message inventory

All rows lack a native **typed semantic MAVLink-M plugin** in the installed SDK.
MavlinkDirect provides generic runtime XML transport. Rows marked unsupported
remain unsupported even though their schemas are present in the pinned snapshot.
This table is a gap inventory, not an implementation plan for each message.

| ID | Message | MAMBA support / evidence |
| --- | --- | --- |
| 53000 | `TRACK_IDENTITY` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53001 | `TARGET_CUE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53002 | `TARGET_HANDOVER` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53003 | `PARTICIPANT_POSITION` | Typed helper; two-way loopback wire acceptance from SITL telemetry; no MCP publisher |
| 53004 | `MAVLINK_M_ACK` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53010 | `TARGET` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53011 | `TARGET_SET_COORD` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53012 | `TARGET_BOX_COORD` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53013 | `TARGET_AUTHORIZATION` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53020 | `FIRES` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53021 | `SPLASH_CORRECTION` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53022 | `BATTLE_DAMAGE_ASSESSMENT` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53023 | `ENGAGEMENT_DIRECTIVE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53024 | `CALL_FOR_FIRE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53030 | `ESAD_STATE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53031 | `ESAD_ARMING` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53032 | `ESAD_CONFIG` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53033 | `STORE_STATUS` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53034 | `STORE_SENSOR_STATUS` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53035 | `STORE_MUNITION` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53036 | `LOITER_MUNITION_CONTROL` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53040 | `RWS_POSE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53041 | `RWS_STATE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53050 | `SENSOR_TASKING` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53060 | `CAS_9LINE` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |
| 53061 | `TERMINAL_CONTROL` | No typed MAMBA mapping; no message-specific interoperability or peer acceptance |

## Own-position field mapping

| Wire field | Source / conversion | Boundary |
| --- | --- | --- |
| `time_usec` | Explicit UTC report-assembly time from caller, in microseconds | Positive uint64; not sensor measurement time |
| `lat`, `lon` | SDK degrees × 1e7, rounded | Latitude ±90 degrees; longitude ±180 degrees; both required |
| `alt` | SDK absolute altitude in metres AMSL | Never substitute relative altitude; unknown stays null/NaN |
| `vx`, `vy`, `vz` | SDK NED velocity in m/s | Positive down; unknown stays null/NaN |
| `course` | No automatic heading inference | Unknown by default; explicit finite values in [0,360) |
| `callsign` | Explicit caller-supplied simulation label | ASCII, 1–49 bytes; no embedded NUL |
| `external_track_number` | Empty by default | ASCII, at most 19 bytes; no embedded NUL |
| `origin_sysid` | Telemetry's selected vehicle ID | Integer 1–255; not an authenticated identity |
| Classification fields | Unknown identity/type and no external namespace by default | Validate pinned enum ranges; no joint-standard gateway mapping implemented |
| MAVLink source header | Configured SDK system/component | Per-message overrides are ignored in the tested native version |

The source schema uses `char[20]` and `char[50]`; the helper reserves a NUL byte.
Unknown float fields use JSON null at the SDK boundary. Raw NaN/Infinity inputs,
oversized float32 values, extra fields and invalid IDs are rejected by the typed
helper. Its native boundary revalidates even values constructed with bypass APIs.

## Custom implementation requirements and unresolved support

The own-position experiment needs no native rebuild. Production integration
still needs a reviewed publisher lifecycle: explicit enablement, connection/session
binding, configured component ownership, telemetry source-age policy, bounded
publication rate, reconnect behavior and recorded outcomes. These policies are
not selected by the experiment, and no agent-facing publication is enabled.

Other message mappings have no typed semantic adapter, MCP interface, peer
capability evidence or message-specific tests. No fields are silently remapped
to standard messages. Any future supported scope must define its semantics and
validation, deterministic state/authorization rules where applicable, lifecycle
and peer acceptance before exposure. Message-specific control implementations
are outside these tickets. ACK handling, retries and routing are not implemented
merely because an ACK schema exists.

Stock ArduCopter is a telemetry source in the test. It is not shown to originate,
consume or act on `PARTICIPANT_POSITION`; the simulated companion publishes to
an independent local decoder. Dynamic flight, real radios/hardware, payloads,
multi-vehicle routing and joint-standard translation remain unvalidated.

See the [compatibility runbook](runbooks/mavlink-m.md),
[acceptance record](testing/mamba-28-29-sitl.md), and
[unmodified schema/provenance](../third_party/mavlink-m/README.md).
