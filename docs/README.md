# Documentation Guide

Only the single-file stdio MCP server and its `ping` tool are implemented. Vehicle, safety, simulation, and hardware capabilities described here remain planned. The [proposal](<../Mamba(revised).pdf>) is the baseline; directory layouts and documentation templates are repository recommendations. TBD means a decision or validated procedure is still required.

| Document | Purpose |
| --- | --- |
| [Architecture](architecture.md) | Component responsibilities and information flow |
| [Requirements and roadmap](requirements.md) | Deliverables, dependencies, dates, and proposal inconsistencies |
| [Safety requirements](safety.md) | Deterministic enforcement and state-model documentation requirements |
| [Development setup](development.md) | Environment and command documentation template |
| [Open decisions](decisions.md) | Unresolved engineering choices and evidence needed |
| [Testing strategy](testing/README.md) | Validation levels, evidence, and benchmark metrics |
| [Acceptance matrix](testing/acceptance-matrix.md) | Feature-to-scenario traceability |
| [Safety test matrix](testing/safety-matrix.md) | Safety-rule-to-scenario traceability |
| [Simulation runbook](runbooks/simulation.md) | Future startup, reset, failure, and shutdown procedure |
| [Hardware runbook](runbooks/hardware.md) | Future incremental hardware validation procedure |
| [Audit review](runbooks/audit.md) | Future audit recording and investigation procedure |

Update affected documents with each implemented feature. Record actual commands and evidence only after validation; never treat this scaffold as a completed operational procedure.
