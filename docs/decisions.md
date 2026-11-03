# Open Decision Register

D01 and D02 are **partially resolved**: the basic server uses Python 3.11+, FastMCP 2, and stdio. uv is selected for environment/dependency management, with a non-package `pyproject.toml` and committed `uv.lock`. Exact dependency resolutions are locked; a Python minor-version pin and broader lifecycle validation remain open. D03, D04, and D12 have partial implementation notes below; other entries remain **open**. Named reviewers below are suggested roles, not assignments. Do not infer selections from directory names or recommendations. Record the outcome, rationale, reviewer, date, evidence, and affected requirements when resolving an entry.

| ID | Decision needed | Evidence / resolution needed | Suggested reviewer |
| --- | --- | --- | --- |
| D01 | Python version and packaging/environment tools (partial: uv, Python 3.11+, non-package project) | Validate supported Python versions; dependencies resolved in `uv.lock` | Maintainers |
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

## MAMBA-2 / F2 implementation decisions

Native `mavsdk.asyncio` from `mavsdk>=4.0.6,<5` is selected (D03); ArduPilot compatibility still needs SITL evidence. pytest is selected as a dev dependency (D04), with no coverage threshold. Startup `--config` selects a strict TOML definition for one endpoint and required expected system ID (D12). Other discovered IDs never replace the target. Discovery timeout is 10 seconds, retry delay 5 seconds, and polling interval 1 second; these are connection defaults, not reviewed vehicle safety/freshness limits. D12 multi-vehicle isolation and identity assurance remain open. See the [connection runbook](runbooks/connection.md) for evidence and limitations.

## MAMBA-26/27 read-only data decisions

Six separate no-argument tools expose information, position, NED velocity, battery, GPS, and health. Telemetry is read on demand with a 10-second deadline; no application telemetry cache or explicit stream-rate changes are introduced. Information returns available identification/version sections with explicit partial errors, or a tool error when neither is available. Pending native information requests are shared within a connection generation and drained before SDK destruction. Enums retain SDK names, non-finite numeric values become null, and received_at records SDK-result receipt, not sensor age. These D07/D11/D12 implementation choices do not resolve future safety freshness, authorization, or multi-vehicle isolation requirements. See the [vehicle data runbook](runbooks/vehicle-data.md).
