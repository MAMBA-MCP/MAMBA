# MAVLink-M XML compatibility — MAMBA-28

## Result and selected path

Native MAVSDK **4.0.6** includes `MavlinkDirectAsync.load_custom_xml`,
`send_message` and `subscribe_message`. The pinned Dronecode XML was accepted
at runtime. `PARTICIPANT_POSITION` was independently encoded/decoded in both
directions with pymavlink 2.4.49. A MAVSDK rebuild, legacy passthrough extension
or custom C++ plugin is **not needed for this position-report wire path**.

Use MavlinkDirect for this experiment, with the narrowly extracted position
schema from [the pinned source](../../third_party/mavlink-m/README.md).
The complete original XML was also loaded successfully by the probe; that is
loader acceptance, not interoperability acceptance for every message. The
original `common.xml` include is not resolved from this repository. The SDK
already has standard definitions; the scoped position fragment is self-contained.

The Python helper [participant.py](../../src/mamba/participant.py) validates
one report and constructs its envelope. It does not start a transport, publish
periodically, accept arbitrary XML from an agent, register an MCP tool, or
implement payload operations. MAMBA's tool catalog remains four read-only tools.

## Reproduce

Prerequisites are the same built ArduCopter checkout and WSL environment as
the [read-only acceptance run](../testing/mamba-26-27-sitl.md). No changes to
the operator's running SITL, MAVProxy routes, or MCP configuration are needed.

```bash
uv sync --locked --group simulation
uv run --locked --group simulation python tests/simulation/validate_mavlink_m.py \
  --ardupilot "$HOME/ardupilot" --output /tmp/mamba-mavlink-m-acceptance
```

Use a new output directory and leave SITL instance **32** unused. The script
launches an isolated disarmed quad at 40 N, 74 W, 125 m AMSL; ports are dynamically
allocated on loopback. It requests telemetry streams, waits for global/home
readiness, and maps current position/velocity. Reports go to a local independent
decoder, **not to the autopilot or an operational network**. Ordinary SDK traffic
is routed to the isolated simulator. The scenario does not arm, move, or write
vehicle parameters. Script cleanup terminates its own simulator and native SDK.

Binding generation is local, using pymavlink from the locked simulation group;
no generator subprocess downloads code or schema at test time. Standard XML
schema validation is disabled for the extracted fragment, but the original
message/enum structure is preserved and checksum-checked. Wire CRC agreement
provides the interoperability evidence. Both peers must use matching definitions.

Expected negative probes log `INVALID_MESSAGE`, malformed-XML errors and a
warning for an unknown field. They are intentional; use the final `passed` flag
and process exit code to assess the run. Output includes `report.json`,
`sitl.log`, the extracted XML and the generated independent decoder.

## Native API observations that affect implementation

| Probe | Observed with native MAVSDK 4.0.6 | MAMBA handling |
| --- | --- | --- |
| Position message before XML load | `INVALID_MESSAGE` | Load pinned definitions explicitly |
| Malformed XML | `ERROR` | Fail setup; do not continue with assumed definitions |
| Full/scoped XML load | Both accepted | Scope application access to the single tested message |
| Unknown JSON field | Warning, successful send; field ignored | Strict model forbids extra fields |
| `origin_sysid=256` | Successful send; wire value wraps to **0** | Reject out-of-range IDs before native call |
| Per-message source override 99/88 | Wire still used configured source **1/191** | Set `Configuration.create_manual(1, 191, False)` in simulation; verify wire identity |
| Unsigned 64-bit timestamp | Exact send at `2**64-1`; exact receive above `2**63` | Preserve integer representation |
| Unknown float | JSON null sends IEEE NaN; incoming NaN becomes null | Keep unknowns explicit; reject nonfinite model inputs |
| Corrupt CRC | No delivery to subscriber | Matching schema/CRC required |

Source IDs are routing labels, not authenticated identities. In the scenario,
autopilot 1/1 and publishing companion 1/191 are distinct components. A reverse
test peer uses 1/192. These are isolated test assignments, not production defaults.
The existing MCP server still uses its ground-station configuration, so this
scenario does not silently change its identity or add publishing behavior.

## Limits and decision

D10 is partially resolved for the pinned own-position experiment: runtime
MavlinkDirect plus a typed semantic adapter is selected. General payload
discovery, capability negotiation, peer support, lifecycle policy, acknowledgments,
operational identity assignments, source-age/freshness rules and application
authorization remain unresolved. Legacy MavlinkPassthrough is deprecated in
MAVSDK v4 and is absent from the installed Python plugin catalog; a custom native
plugin remains an option only if a demonstrated future requirement needs it.

The [mapping matrix](../mavlink-m-mappings.md) distinguishes wire schema loading
from semantic implementation. The [MAMBA-29 acceptance record](../testing/mamba-28-29-sitl.md)
contains exact run evidence. No hardware or joint-standard interoperability
claim follows from this local test. The pinned dialect itself marks some identity
and participant-type values as provisional; the helper defaults to unknown
classification and no external track number.

## Primary references

- [MAVSDK Python MavlinkDirect guide](https://mavsdk.mavlink.io/main/en/python/mavlink_direct.html)
- [Runtime versus compile-time behavior and passthrough deprecation](https://mavsdk.mavlink.io/main/en/cpp/guide/mavlink_direct.html)
- [Pinned Dronecode dialect revision](https://github.com/Dronecode/mavlink-military/tree/23cec36751681aa281c1e5ca6b222a07c6c0c002)

The installed binding source and recorded native run establish version-specific
behavior; upstream main documentation alone does not establish 4.0.6 validation.
