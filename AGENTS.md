# Repository Guidelines

## Project Scope & Architecture
MAMBA is a Python MCP server for AI-agent integration with MAVLink vehicles and planned MAVLink-M payloads. Use `Mamba(revised).pdf` as the baseline; distinguish planned from implemented capabilities. Reference feature names alongside IDs because proposal numbering differs.

Preserve the proposed command path: MCP tools → deterministic safety layer → MAVSDK/protocol adapters → vehicle. Enforce configuration-driven vehicle and payload state machines, authorization, sequencing, and rate limits outside the AI agent. Reject operations when required state is missing, stale, or inconsistent. Maintain independent connections, telemetry, and safety state per vehicle. Treat MAVLink-M adapters as stubs until implemented and validated.

## Project Structure & Module Organization
The stdio MCP server lives in `src/mamba/server.py`, exposing `ping`, read-only `get_vehicle_status`, read-only `get_vehicle_information`, and consolidated read-only `get_vehicle_telemetry(fields)` (MAMBA-26 / MAMBA-27). It supports optional configured MAVSDK v4 asyncio discovery for one expected vehicle ID (MAMBA-2 / F2); SITL acceptance remains pending. Keep FastMCP setup, tools, and CLI startup in `server.py`; connection configuration, discovery, status types, and SDK lifecycle live in `src/mamba/connection.py`. Information/telemetry retrieval and typed responses live in `src/mamba/vehicle_data.py`. Vehicle commands and safety capabilities remain planned. `tests/` reserves unit, integration, simulation, and hardware tests. `config/` reserves validated vehicle/payload definitions; `simulation/` and `benchmarks/` reserve scenarios and assets. Empty directories contain `.gitkeep`, not functioning modules.

Start with [docs/README.md](docs/README.md). Update requirements, matrices, and runbooks with implementation. Track open decisions in [docs/decisions.md](docs/decisions.md).

## Build, Test, and Development Commands
Use Python 3.11+ with FastMCP 2 (`fastmcp>=2,<3`). Use uv with `pyproject.toml` and `uv.lock`; pytest is configured for unit and stdio integration tests.

- `uv sync --locked`: create/update `.venv` from the lockfile.
- `uv run --locked python src/mamba/server.py`: start the stdio server.
- `uv add <dependency>`: update dependencies; commit manifest and lockfile together.
- `git diff --check`: check whitespace.

Record validated commands in [docs/development.md](docs/development.md) and runbooks. TBD procedures are not operational.

## Coding Style & Naming Conventions
Use four-space Python indentation, `snake_case` functions/modules, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants. Prefer explicit tool schemas, typed interfaces, and small modules. No formatter or linter is currently configured; record chosen tooling in project configuration before requiring it.

## Testing Guidelines
Use `uv run --locked pytest -q` for tests in `test_*.py` files. No coverage threshold exists yet. Map tests to proposal acceptance criteria, covering state transitions, authorization, stale telemetry, disconnections, manual override, and vehicle-routing isolation. Record rejection reasons and timing metrics. Complete applicable simulation tests before incremental hardware testing, beginning with identity checks and telemetry.

## Commit & Pull Request Guidelines
Use concise imperative commit subjects. PRs should describe changes, reference proposal feature names and appendix IDs or issues, report validation, and identify limitations. Include screenshots for operator-interface changes. Preserve unresolved proposal gaps explicitly; documentation coverage does not establish acceptance.
