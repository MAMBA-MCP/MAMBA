# Safety Test Matrix

All scenarios below are planned and unexecuted. Rule IDs reference [safety requirements](../safety.md); feature IDs use appendix numbering. Concrete parameters and validated operating envelopes are TBD.

| Rule | Features / scenarios | Required observations |
| --- | --- | --- |
| S1 — Authoritative state | F7/F15/F16; A07/A15/A16: unknown, stale, conflicting or lost telemetry; disconnect during transition | No state-changing transmission when required evidence is unreliable; structured explanation and audit entry; state remains tied to actual observations |
| S2 — Operating envelope | F7/F15/F18; A07/A15/A18: valid/invalid transitions, wrong platform, vehicle/payload conflict | Valid operations allowed; invalid or unsupported operations stop before execution; correct model and host dependencies evaluated |
| S3 — Sequencing/timing | F9/F16; A09/A16: valid sequence, simultaneous conflicts, excessive rate, unfinished transition, timeout | Deterministic decision, no overlapping conflicting operations; configured limits and completion requirements enforced |
| S4 — Human authorization | F11/F16; A11/A16: approve, deny, expire, reuse, alter parameters, unauthorized approver, disconnect while pending | Only specifically approved operation can proceed; all listed invalid cases prevent execution and are visible in audit evidence |
| S5 — Manual override | F13/F16/F17; A13/A16/A17: override during agent work and subsequent requests | Manual control takes priority; pending commands canceled/safely suspended, new agent changes rejected, no automatic regain; visible/logged status |
| S6 — Vehicle isolation | F20; A20: two vehicles, invalid/duplicate identity, concurrent requests, one disconnect, different valid states | No mixed telemetry/state or cross-target transmission; remaining vehicle unaffected by peer disconnect |
| S7 — Auditability | F4/F11/F13/F16; A04/A11/A13/A16: success, rejection, execution failure, unwritable log destination | Trace reconstructs requests, decisions, transitions, approvals and outcomes; failures detectable; sensitive authorization material not unnecessarily exposed |

Each negative scenario needs transmission-boundary evidence that the rejected action did not reach MAVSDK or the payload as applicable. Add reviewed platform-specific cases after operating envelopes are defined. No numeric limits or acceptance thresholds are implied by this matrix.
