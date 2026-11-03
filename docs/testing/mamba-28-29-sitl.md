# MAMBA-28/29 simulation acceptance

Executed on 2026-11-03 in Ubuntu 24.04 / WSL2, Python 3.12.3, native MAVSDK
4.0.6 and pymavlink 2.4.49. MAMBA base: `8c67f1f041d3fc6ec947dc0f8077f9850ea15d15`.
ArduPilot source checkout: `9165d22419406556fc9815d9f4e3e299e13713a8`.
The exact existing binary SHA-256 and executed command are in the
[retained JSON evidence](evidence/mamba-28-29-wsl.json); source HEAD alone does
not prove the provenance of a pre-existing build.

Run interval: `2026-11-03T19:35:13.030657+00:00` to `2026-11-03T19:35:34.650656+00:00`.
Result: **passed**. Reproduce with the [compatibility runbook](../runbooks/mavlink-m.md).

## Executed path

1. Launch separate ArduCopter instance 32 with loopback-only routing and a fresh
   output/EEPROM directory. The operator's existing instance is not used.
2. Discover configured autopilot 1/1 through the existing connection monitor,
   using an explicitly configured companion SDK identity of 1/191.
3. Request standard telemetry and wait for global/home estimator readiness.
4. Confirm `PARTICIPANT_POSITION` is unavailable before XML loading and malformed
   XML is rejected. Load both full pinned XML and a self-contained scoped fragment.
5. Map MAMBA position/velocity observations into the typed report; compare scaled
   coordinates against an independently decoded `GLOBAL_POSITION_INT` frame.
6. Send the report through native MavlinkDirect to a local pymavlink decoder.
   Check field values, frame source IDs, full uint64 timestamp and CRC extra.
7. Check boundary payloads and native encoder validation gaps, then inject an
   independently encoded report from 1/192 back into the native subscriber.
8. Reject a corrupted CRC, receive the valid frame, preserve unknown float values,
   close subscriptions/plugins, and terminate only the test's simulator.

## Results and concrete observations

| Check | Result |
| --- | --- |
| Message identity | ID **53003**, CRC extra **126** |
| SITL coordinates | 40.0000000 N, 74.0000000 W; wire latitude 400000000 and longitude -740000000 |
| Absolute altitude | Approximately 125.09 m AMSL; relative altitude not substituted |
| Normal sender | MAVLink source 1/191; `origin_sysid=1` |
| Nonzero protocol velocities | North +1.25, east −2.5, down +0.75 m/s preserved |
| Boundary payload | ±coordinate boundaries, negative altitude, 49/19-character arrays and `2**64-1` timestamp preserved |
| Reverse decoding | Source 1/192, timestamp above `2**63`, null/NaN values and nonzero velocity preserved |
| Corrupt packet | Bad CRC not delivered; following valid packet delivered |
| Unknown native field | Accepted but omitted; adapter rejects it |
| Byte overflow | Native 256 wrapped to 0; adapter rejects it |
| Source override probe | Per-message 99/88 still emitted as configured 1/191 |
| Connection/cleanup | Connection remained valid; simulator exited with code 0 |

Unit and regression verification: **112 tests passed in 19.74s**, with the two
existing upstream Authlib warnings. New unit coverage validates schema integrity,
field bounds, ASCII arrays, unknown values, nonzero axis conversion, absent data,
and rejection of invalid model-copy values before the native boundary.
The existing MCP integration tests still assert exactly four read-only tools.

## Acceptance boundaries

This accepts runtime loading and two-way local wire compatibility for the pinned
own-position schema. It does not accept every message in the full dialect,
stock-autopilot native MAVLink-M behavior, autonomous publishing, operational
classification, flight/hardware operation, or all of F12/F14. The simulator is
stationary; nonzero velocity signs were tested with explicit protocol samples.
Timestamp evidence concerns report assembly and serialization, not sensor age.
Payload/state-machine/authorization features remain planned.

Raw run assets remain in `/tmp/mamba-mavlink-m-final` and may be cleared by the
host. Retained evidence includes the actual wire frames and source observations.
