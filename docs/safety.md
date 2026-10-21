# Safety Design Requirements

Source: proposal §4 and appendix UAV state machine, sequencing, authorization, manual override, payload, and platform-extension features. These are requirements for future implementation, not an operational safety configuration.

## Required enforcement

| Rule | Required behavior |
| --- | --- |
| S1 — Authoritative state | Derive vehicle/payload state from telemetry; reject when required state is unknown, stale, inconsistent, or disconnected |
| S2 — Operating envelope | Evaluate requested actions against the correct platform/payload state, valid transitions, operating constraints, and vehicle dependencies before transmission |
| S3 — Sequencing and timing | Enforce deterministic ordering, completion requirements, rate limits, and timing; prevent concurrent conflicting state-changing operations |
| S4 — Human authorization | Require explicit valid operator approval for designated actions; bind approval to the particular operation and parameters |
| S5 — Manual override | Give manual control priority, cancel or safely suspend pending agent commands, reject new agent state changes, and prevent automatic return to agent control |
| S6 — Vehicle isolation | Route only to the identified vehicle and maintain independent state, telemetry, sequencing, and authorization |
| S7 — Auditability | Record requests, decisions/reasons, transitions, authorization, and execution outcomes; make logging failures detectable |

The AI agent cannot supply the safety decision or substitute its own interpretation for deterministic enforcement. A denied operation must not reach the vehicle/payload execution path.

## State-model documentation template

Before implementing each supported platform/payload, record:

- Requirement source, reviewer, version, supported platform, and associated payload/vehicle.
- State definitions and telemetry evidence, including freshness and inconsistency handling.
- A reviewed state diagram and transition table: source state, requested action/event, required conditions, authorization, expected completion evidence, destination, and rejection reason.
- Operating envelope, environmental limitations, timing constraints, and loss-of-connection behavior.
- Permitted tools per state, manual-control behavior, recovery conditions, and linked test scenarios.

The proposal lists representative UAV states such as disconnected, disarmed, armed, airborne, landing, and emergency/error. These are examples, not a complete validated state model. No transition diagram, environmental threshold, timeout, or executable configuration is established here. USV/UGV models must avoid UAV-only assumptions.

## Authorization and override requirements

The operator must see the action, parameters, and affected vehicle/payload before approval. Denied, expired, reused, parameter-modified, or unauthorized approvals must not permit execution. Loss of communication while approval is pending must not allow the protected operation to execute. Define the actual lifetime, identity mechanism, invalidation, and revalidation behavior before implementation.

Manual-override status must remain visible and vehicle state synchronized. Document a deliberate procedure for restoring agent control; it must not resume automatically.

Track unresolved policies in [open decisions](decisions.md) and validate these rules using the [safety test matrix](testing/safety-matrix.md).
