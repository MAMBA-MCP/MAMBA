# Open Decision Register

All entries are **open**. Named reviewers below are suggested roles, not assignments. Do not infer selections from directory names or recommendations. Record the outcome, rationale, reviewer, date, evidence, and affected requirements when resolving an entry.

| ID | Decision needed | Evidence / resolution needed | Suggested reviewer |
| --- | --- | --- | --- |
| D01 | Python version and packaging/environment tools | Reproducible environment compatible with selected SDKs | Maintainers |
| D02 | MCP SDK, transport, client/session lifecycle | Tool discovery, errors, reconnection, and client compatibility trial | Maintainers |
| D03 | Dependency versions and MAVSDK/ArduPilot/Gazebo compatibility | Validated simulation version matrix and installation procedure | Simulation lead |
| D04 | Test, formatting, lint/type tooling and coverage policy | Agreed commands and meaningful validation criteria | Maintainers |
| D05 | Operator interface and agent integration | Input/output, telemetry, notifications, approval and override workflow | Team and customer |
| D06 | Vehicle/payload operating envelopes and state models | Customer/SME-reviewed states, transitions, limitations, telemetry evidence | Customer and SMEs |
| D07 | Freshness, timing, rate limits, queueing and completion | Per-platform requirements and deterministic concurrency/failure tests | Safety reviewers |
| D08 | Authorization identity, protected actions, lifetime and invalidation | Operation-specific approval and replay/expiry/parameter-change tests | Customer and safety reviewers |
| D09 | Manual override and deliberate agent-control restoration | Queue handling, operator control path, state synchronization procedure | Customer and safety reviewers |
| D10 | MAVLink-M dialect/version and SDK extension mechanism | Compare passthrough/direct messaging versus custom plugin; validate encoding, decoding, discovery/addressing | Integration lead |
| D11 | Tool catalog and semantic granularity | Model-context and tool-selection benchmarks across representative agents | Team |
| D12 | Vehicle identifiers, discovery and lifecycle | Two-vehicle routing/isolation and disconnect behavior evidence | Integration lead |
| D13 | Audit format, storage, retention, redaction and failure behavior | Reconstructable chronological trace; detectable storage/write failures | Maintainers and safety reviewers |
| D14 | Simulator models, payload representation, reset and benchmark methods | Repeatable scenarios with documented physical/simulated differences | Simulation lead |
| D15 | Hardware readiness and F19 acceptance criteria | Approved equipment/procedure, applicable simulation evidence, explicit F19 scope | Customer and test reviewers |
| D16 | Proposal numbering and schedule reconciliation | Confirm F7/F8 mapping, missing F19 detail, current ownership and milestones | Team and customer |

No numeric operating limits, approval lifetime, protocol schema, or implementation mechanism is selected by this scaffold.
