# Documentation Guide

The stdio MCP server (`src/mamba/server.py`) delegates connection configuration, discovery, and SDK lifecycle to `src/mamba/connection.py`. `src/mamba/vehicle_data.py` supplies on-demand information and telemetry retrieval. Together they implement `ping`, configured native MAVSDK v4 asyncio discovery, connection status (MAMBA-2 / F2), and separate information plus consolidated selected-field telemetry tools (MAMBA-26 / MAMBA-27; F2 and the read-only portion of F3). Automated tests and narrow read-only ArduPilot SITL scenarios cover retrieval and failures. MAMBA-28/29 add a pinned XML compatibility experiment and a typed own-position helper with independent wire acceptance; MAMBA-30 records unsupported mappings. Vehicle commands, safety, Gazebo/payload integration, and hardware capabilities remain planned. The [proposal](<../Mamba(revised).pdf>) is the baseline; directory layouts and documentation templates are repository recommendations. TBD means a decision or validated procedure is still required.

| Document | Purpose |
| --- | --- |
| [Architecture](architecture.md) | Component responsibilities and information flow |
| [Requirements and roadmap](requirements.md) | Deliverables, dependencies, dates, and proposal inconsistencies |
| [Safety requirements](safety.md) | Deterministic enforcement and state-model documentation requirements |
| [Development setup](development.md) | Environment and command documentation template |
| [MAVLink-M compatibility](runbooks/mavlink-m.md) | Runtime XML findings and own-position scenario |
| [Message support matrix](mavlink-m-mappings.md) | Implemented and unsupported mappings |
| [Open decisions](decisions.md) | Unresolved engineering choices and evidence needed |
| [Testing strategy](testing/README.md) | Validation levels, evidence, and benchmark metrics |
| [Acceptance matrix](testing/acceptance-matrix.md) | Feature-to-scenario traceability |
| [Safety test matrix](testing/safety-matrix.md) | Safety-rule-to-scenario traceability |
| [Vehicle data](runbooks/vehicle-data.md) | Read-only tool fields, timeouts, lifecycle, and pending SITL acceptance |
| [Vehicle connection](runbooks/connection.md) | Startup TOML, status tool, recovery, and pending SITL acceptance |
| [Simulation runbook](runbooks/simulation.md) | Future startup, reset, failure, and shutdown procedure |
| [Hardware runbook](runbooks/hardware.md) | Future incremental hardware validation procedure |
| [Audit review](runbooks/audit.md) | Future audit recording and investigation procedure |

Update affected documents with each implemented feature. Record actual commands and evidence only after validation; never treat this scaffold as a completed operational procedure.
