# Future Source Layout

No Python package or application exists here; directories reserve responsibilities from the proposal. Do not infer imports or public interfaces from these names.

| Directory | Future responsibility |
| --- | --- |
| [tools/](tools/) | MCP tool discovery, semantic operations, validation, structured results |
| [safety/](safety/) | State machines, operating envelopes, authorization, sequencing and override |
| [adapters/](adapters/) | MAVSDK connectivity and MAVLink/MAVLink-M abstractions |
| [telemetry/](telemetry/) | Vehicle-specific observations, freshness and state evidence |
| [audit/](audit/) | Chronological request/decision/result recording |
| [operator/](operator/) | Operator-facing integration; UI technology and placement TBD |

See [architecture](../../docs/architecture.md) before adding implementation. All state-changing tools must pass deterministic safety enforcement before execution.
