# Feature Acceptance Matrix

Source: proposal §9, except F19 (release table only). IDs follow the appendix; see [numbering reconciliation](../requirements.md). These are summarized acceptance scenarios, not executable tests or exhaustive replacements for the proposal. Every row is **not run / not implemented**. The level allocation and scenario IDs below are organizational recommendations. Evidence requirements are defined in the [testing plan](README.md).

| Feature | Scenario ID / planned levels | Acceptance focus |
| --- | --- | --- |
| F1 — MCP foundation | A01; integration | Start server, connect client, discover/invoke test tool; invalid requests and tool failures remain controlled; reconnect without server restart |
| F2 — Vehicle connection | A02; integration, simulation | Discover and retain vehicle connection, expose status, detect disconnect without server failure; handle timeout, bad URI, and multiple systems |
| F3 — Basic tools | A03; integration, simulation | Return health/position/altitude/battery; permitted arm/disarm/takeoff/land/return-to-launch; invalid parameters, unavailable telemetry and SDK failures return useful structured errors |
| F4 — Audit trail | A04; integration | Successful, rejected and failed calls have chronological timestamps, appropriate arguments, responses and outcomes sufficient to reconstruct sequence; detect logging failures |
| F5 — Simulation pipeline | A05; simulation | Start Gazebo/SITL, connect through MAVSDK/MAMBA, obtain telemetry and execute basic simulated commands; reproducible restart; controlled startup/port/termination failures |
| F6 — Initial testing | A06; simulation | Agent discovers/selects basic tools, obtains telemetry and executes valid navigation; invalid requests/arguments, unhealthy state, disconnect and SDK failures handled |
| F7 — UAV state machine | A07; unit, integration, simulation | State reflects telemetry; valid transitions permitted; invalid/unknown/stale/inconsistent-state operations rejected before MAVSDK with logged explanations |
| F8 — Advanced navigation | A08; integration, simulation | Discover/select advanced tools, execute a valid multi-action mission, observe progress; reject/report invalid or interrupted mission operations |
| F9 — Sequencing/timing | A09; unit, simulation | Valid sequences succeed; conflicting concurrent commands, excessive call rate, premature transitions and timeouts produce deterministic enforcement and structured feedback |
| F10 — Operator interface | A10; integration, simulation | Submit natural-language intent, show agent response, connection status, telemetry and notifications; clearly present backend/agent/vehicle failures |
| F11 — Authorization | A11; unit, integration, simulation | Protected operation waits for operator; denial prevents execution; approval permits only intended action; expiry, reuse, changed parameters, unauthorized approval or pending communication loss do not execute protected operation; log activity |
| F12 — MAVLink-M stubs | A12; unit, integration | Document/test abstraction and supported message representation against harness; encoding/decoding/dialect/component/response errors controlled; clearly identify stub limitations |
| F13 — Manual override | A13; unit, integration, simulation | Override takes precedence; cancel/safely suspend pending agent commands, reject new state changes, permit manual control, show/log status; no automatic agent takeover |
| F14 — Payload simulation | A14; integration, simulation | Initialize representative payload, send supported MAVLink-M operation, return status; unsupported/unavailable/delayed/fault cases controlled; document simulation limits |
| F15 — Payload state machines | A15; unit, simulation | Valid operation succeeds; invalid transition, vehicle-state conflict, missing authorization, unknown/stale/disconnected payload rejected before transmission; log transitions/reasons |
| F16 — Safety benchmark | A16; simulation | Repeat valid and invalid state, concurrency, rate, authorization, stale telemetry, disconnect, payload-failure and manual-override scenarios; collect decisions/reasons, latency, sequence/transition correctness and agent response; required safety tests pass |
| F17 — Hardware pipeline | A17; hardware after simulation | Follow approved pre-test procedure, identify physical vehicle, verify telemetry-only path, then approved low-risk action; retain safety enforcement, manual override and audit evidence |
| F18 — USV/UGV states | A18; unit, integration, simulation or approved test interface | Select correct UAV/USV/UGV state model; valid class-specific actions succeed; incompatible tools/transitions rejected; shared infrastructure works without UAV-only assumptions |
| F19 — Hardware testing | A19; hardware, criteria TBD | No detailed appendix acceptance section; define scope, prerequisites, scenarios and evidence with stakeholders before claiming coverage or completion |
| F20 — Multi-UAS | A20; integration, simulation | Two SITL vehicles have unique identities and independent telemetry/state; route commands correctly, retrieve individual/combined information, reject invalid identifiers, isolate disconnects and simultaneous requests |

## Completion record

When executable scenarios exist, link each scenario ID to its test/scenario artifact and record run evidence, pass/fail, exceptions, and reviewer. Until then, all rows remain planning coverage only.
