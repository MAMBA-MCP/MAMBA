# Testing and Evidence Plan

pytest is a development dependency; run `uv run --locked pytest -q` for F1 stdio, F2 (MAMBA-2) connection/configuration tests, and MAMBA-26/27 read-only information/telemetry tests (F2 / partial F3). See the [connection evidence and limitations](../runbooks/connection.md). Benchmark runners and coverage thresholds remain TBD; SITL and hardware acceptance have not been run.

## Validation levels

| Level / reserved location | Planned purpose |
| --- | --- |
| [Unit](../../tests/unit/) | Deterministic state evaluation, transition validity, timing/authorization rules, argument handling, and routing decisions with controlled inputs |
| [Integration](../../tests/integration/) | MCP discovery/errors/reconnection, adapter contracts, telemetry propagation, operator/audit interaction, and failure isolation |
| [Simulation](../../tests/simulation/) | Agent-to-Gazebo/ArduPilot SITL workflows, payload simulation, concurrency, failures, and repeatable benchmarks |
| [Hardware](../../tests/hardware/) | Incremental identity/telemetry and approved command validation after applicable simulation passes |

Unit/integration allocation is a repository planning recommendation. Proposal acceptance is traced in the [feature matrix](acceptance-matrix.md); safety-specific coverage is traced in the [safety matrix](safety-matrix.md).

## Scenario and evidence template

For every future scenario record its ID, feature name/ID, safety rules, objective, prerequisites, exact environment/version/configuration, initial vehicle/payload state, steps and fault injection, expected decisions and observable outcomes, cleanup/reset, and known limitations. Record a run identifier, timestamp, revision, actual outcome, audit/result references, and reviewer. Use controlled time and repeatable inputs where needed; the mechanism is TBD.

Verify rejection at the adapter/transmission boundary, not solely through operator-visible text. Distinguish a submitted/acknowledged command from a completed action. Keep expected failures and infrastructure failures identifiable.

## Benchmark metrics

The proposal calls for accepted/rejected command counts, rejection reasons, safety-layer processing latency, sequence correctness, transition correctness, and agent behavior after rejection. Also evaluate tool catalog organization and tool-selection effectiveness as described in §4.

Record metric definitions, measurement boundaries, units, workload, sample counts, raw evidence references, and environment. Summarize latency distributions and repeatability when collecting data; methods and pass thresholds remain TBD. Do not publish fabricated baseline numbers or treat metrics as passed acceptance criteria without agreed targets.

## Gates

Initial simulation must demonstrate tool discovery, telemetry, basic commands, and controlled failures. Expanded simulation must cover authorization, sequencing, payload constraints, manual override, and multi-vehicle isolation as applicable. Applicable simulation validation precedes physical testing. F19 acceptance needs stakeholder definition; this plan supplies no substitute hardware criteria.
