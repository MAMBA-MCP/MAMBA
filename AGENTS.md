# Repository Guidelines

## Project Scope & Architecture
MAMBA is a Python MCP server bridging model-agnostic AI agents with MAVLink vehicles and planned MAVLink-M payload support. Use `Mamba(revised).pdf` as the proposal baseline; distinguish proposed features from implemented capabilities. Its release table and appendix differ in some feature numbering, so reference feature names alongside IDs.

Preserve the proposed command path: MCP tools → deterministic safety layer → MAVSDK/protocol adapters → vehicle. Enforce configuration-driven vehicle and payload state machines, authorization, sequencing, and rate limits outside the AI agent. Reject operations when required state is missing, stale, or inconsistent. Maintain independent connections, telemetry, and safety state per vehicle. Treat MAVLink-M adapters as stubs until implemented and validated.

## Project Structure & Module Organization
This is a documentation scaffold with no application code or executable tests. `src/mamba/` reserves tools, safety, adapters, telemetry, audit, and operator integration. `tests/` reserves unit, integration, simulation, and hardware tests. `config/` reserves validated vehicle/payload definitions; `simulation/` and `benchmarks/` reserve scenarios and assets. Empty directories contain `.gitkeep`, not functioning modules.

Start with [docs/README.md](docs/README.md). Update requirements, matrices, and runbooks with implementation. Track open decisions in [docs/decisions.md](docs/decisions.md).

## Build, Test, and Development Commands
No build system, dependency manifest, application entry point, or test runner is configured yet.

- `python3 -m venv .venv`: create an isolated Python environment.
- `source .venv/bin/activate`: activate it in Bash.
- `git diff --check`: check changes for whitespace errors.

Record validated commands in [docs/development.md](docs/development.md) and runbooks. TBD procedures are not operational.

## Coding Style & Naming Conventions
Use four-space Python indentation, `snake_case` functions/modules, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants. Prefer explicit tool schemas, typed interfaces, and small modules. No formatter or linter is currently configured; record chosen tooling in project configuration before requiring it.

## Testing Guidelines
No framework or coverage threshold exists yet. Prefer pytest with `test_*.py` files when adding tests. Map tests to proposal acceptance criteria, covering state transitions, authorization, stale telemetry, disconnections, manual override, and vehicle-routing isolation. Record rejection reasons and timing metrics. Complete applicable simulation tests before incremental hardware testing, beginning with identity checks and telemetry.

## Commit & Pull Request Guidelines
History contains only `Initial commit`; no established commit convention exists. Use concise imperative subjects. PRs should describe changes, reference proposal feature names and appendix IDs or issues, report validation, and identify limitations. Include screenshots for operator-interface changes. Preserve unresolved proposal gaps explicitly; documentation coverage does not establish acceptance.
