# Requirements and Roadmap

Source: [proposal](<../Mamba(revised).pdf>) §2.2, §5, and §9. All rows are **planned / not implemented**. Dates reproduce the original release plan and are not completion claims or renewed commitments.

## Core deliverables

1. MCP server with discoverable MAVLink/MAVLink-M command and telemetry tools.
2. State machines for supported vehicle platforms and payloads.
3. Simulation test platform for benchmarking.
4. Evidence evaluating effectiveness and viability in simulation and on hardware.

## Source reconciliation

Use **appendix feature IDs plus feature names** throughout this scaffold. The release table assigns F7 to advanced navigation and F8 to the UAV state machine; the appendix reverses them. Both have the same target date. Dependencies below follow the appendix. F19 appears only in the release table: its prerequisites and detailed acceptance criteria remain undefined. Resolve these discrepancies with the project stakeholders before baselining implementation tickets.

## Feature roadmap

| Appendix ID | Feature / intended deliverable | Appendix prerequisites | Original target |
| --- | --- | --- | --- |
| F1 | MCP foundation: server lifecycle, tool discovery, invocation, controlled errors | None | 2026-10-23 |
| F2 | Persistent MAVSDK vehicle connection and availability tracking | F1 | 2026-10-23 |
| F3 | Basic telemetry and navigation tools | F1, F2 | 2026-11-06 |
| F4 | Chronological action logging and audit trail | F1, F3 | 2026-11-06 |
| F5 | Repeatable Gazebo / ArduPilot SITL simulation pipeline | F2, F3 | 2026-11-30 |
| F6 | Initial agent-driven basic navigation and failure testing | F1–F5 | 2026-11-30 |
| F7 | UAV safety state machine (release table F8) | F3, F4, F5 | 2026-12-06 |
| F8 | Advanced navigation and mission planning (release table F7) | F3, F5, F7 | 2026-12-06 |
| F9 | Deterministic sequencing and timing enforcement | F7, F8 | 2026-12-20 |
| F10 | Initial human operator interface | F1, F3 | 2027-01-20 |
| F11 | Human confirmation and authorization through interface | F7, F9, F10 | 2027-01-20 |
| F12 | MAVLink-M abstraction/stubs in MAVSDK integration | F2, F3 | 2027-02-06 |
| F13 | Manual override | F7, F9, F10 | 2027-02-06 |
| F14 | MAVLink-M representative payload simulation in Gazebo | F5, F12 | 2027-02-20 |
| F15 | Payload state machines and vehicle-state dependencies | F7, F12, F14 | 2027-02-20 |
| F16 | Safety testing and benchmarking in simulation | F7, F9, F11, F15 | 2027-03-05 |
| F17 | Incremental hardware testing pipeline | F16 and applicable simulation tests passed | 2027-03-19 |
| F18 | USV and UGV state machines | F7, F9; stable state-machine abstraction | 2027-03-19 |
| F19 | Hardware testing; detailed deliverable TBD | Not specified | 2027-03-30 |
| F20 | Multi-UAS management and command routing | F2, F3, F7, F9 | 2027-04-14 |

## Planning guidance

Implement against feature names and dependencies rather than calendar order alone. Foundational simulation work precedes expanded safety validation; applicable simulation tests must pass before hardware testing. Multi-UAS is a later proposal feature, but independent vehicle identity/state is an architectural requirement.

Before a feature is considered complete, update its behavior and limitations documentation, execute its applicable [acceptance scenarios](testing/acceptance-matrix.md), and retain the resulting evidence. Feature ownership, current scheduling, and issue links are not assigned by this scaffold.
