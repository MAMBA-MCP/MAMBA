# MAMBA

MCP-enabled Autonomous MAVLink-M Bridge for AI.

MAMBA is a proposed Python MCP server that connects model-agnostic AI agents to MAVLink vehicles and MAVLink-M payload capabilities. A deterministic safety layer evaluates requests before vehicle execution; telemetry and structured results return to the agent and operator.

## Current status

This repository contains a **documentation scaffold only**. Application code, executable tests, dependencies, runtime configuration, simulator integrations, and hardware support have not been implemented. Empty directories reserve locations for future work; their names are organizational recommendations rather than functioning modules.

The [proposal](<Mamba(revised).pdf>) is the requirements baseline. Its dates are original planning targets, not current commitments or evidence of completion. MAVLink-M support is planned initially through stubs and simulation; actual dialect and SDK compatibility remain to be established.

## Start here

1. Read [Repository Guidelines](AGENTS.md) and [architecture](docs/architecture.md).
2. Review the [requirements and roadmap](docs/requirements.md), [safety requirements](docs/safety.md), and [open decisions](docs/decisions.md).
3. Use the [acceptance matrix](docs/testing/acceptance-matrix.md) to plan feature validation.
4. Fill in the [development setup](docs/development.md) and applicable [runbooks](docs/README.md) when implementing a feature. No server or test command is available yet.

## Repository map

| Location | Intended contents |
| --- | --- |
| [src/mamba/](src/mamba/README.md) | Future MCP tools, safety logic, protocol adapters, telemetry, audit, and operator integration |
| [config/](config/README.md) | Future validated vehicle and payload safety definitions |
| [tests/](tests/README.md) | Future unit, integration, simulation, and hardware tests |
| [simulation/](simulation/README.md) | Future repeatable environments and scenarios |
| [benchmarks/](benchmarks/README.md) | Future measurement scenarios and analysis |
| [docs/](docs/README.md) | Architecture, requirements, procedures, and planning records |

## Development

Python is specified by the proposal; its version, package manager, MCP transport, and testing/linting tools are undecided. See [development setup](docs/development.md) for the information that must be recorded before reproducible installation is possible. `git diff --check` checks whitespace in tracked changes; it does not validate project functionality.

Complete applicable simulation validation before incremental hardware testing. See the [hardware runbook template](docs/runbooks/hardware.md).

## License

[MIT](LICENSE).
