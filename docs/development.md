# Development Setup Template

Status: a single-file MCP server exists at `src/mamba/server.py`, using the official SDK v2 and stdio transport. It exposes only `ping`, returning `pong`. uv manages dependencies in `pyproject.toml`, resolved versions in `uv.lock`, and the local `.venv`. MAVSDK is declared for future integration. No vehicle integration, package build, test runner, formatter, or linter exists. Remaining TBD commands are planning placeholders.

## Environment record to complete

| Item | Required record | Current value |
| --- | --- | --- |
| Host | Supported OS, architecture, resource requirements | TBD |
| Python | Version and environment/package management | Python 3.11+; uv-managed `.venv` |
| MCP | SDK version, transport, client configuration | Official SDK v2 (`mcp>=2,<3`), stdio; client launch below |
| MAVSDK | Version, backend requirements, connection methods | `mavsdk>=4.0.6,<5`; exact version in `uv.lock`; integration TBD |
| ArduPilot | SITL and physical firmware versions/configuration | TBD |
| Gazebo | Version, model/world assets, integration dependencies | TBD |
| MAVLink-M | Dialect/version, generation tools, integration mechanism | TBD |
| Quality tooling | Test framework, formatter, lint/type checks, coverage policy | TBD |

## Command inventory to complete after validation

Record the command, working directory, prerequisites, configuration inputs, expected output, and cleanup for each operation:

| Operation | Command |
| --- | --- |
| Install dependencies | `uv sync --locked` from repository root |
| Start MCP server | `uv run --locked python src/mamba/server.py` from repository root; stdio client required |
| Start operator interface | TBD — interface technology undecided |
| Run unit and integration tests | TBD — no executable tests |
| Start / stop / reset simulation | TBD — see [simulation template](runbooks/simulation.md) |
| Run safety scenarios and benchmarks | TBD — no runner exists |
| Format, lint, type-check, and build | TBD — no tooling configured |

## Run the basic server

```bash
uv sync --locked
uv run --locked python src/mamba/server.py
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use Python 3.11+ for the [official SDK v2](https://py.sdk.modelcontextprotocol.io/). The process waits for MCP messages on stdin; stdout carries protocol traffic. A client can launch `uv` with arguments `run --locked --project /absolute/path/to/MAMBA python /absolute/path/to/MAMBA/src/mamba/server.py`; use the absolute uv executable path if the client does not inherit your shell PATH. No HTTP endpoint, environment variables, or vehicle configuration is needed. Call `ping` with `{}` to receive `pong`. Stop a manually launched process with Ctrl+C; a client manages its subprocess lifecycle.

Keep protocol stdout free of diagnostic prints. Exact dependency versions are recorded in `uv.lock`. `git diff --check` checks whitespace in tracked changes.

## Dependency workflow

Use `uv add <dependency>` and `uv remove <dependency>` to change requirements. Use `uv lock --upgrade-package <dependency>` for an intentional upgrade, then `uv sync --locked`. Commit `pyproject.toml` and `uv.lock` together. `uv lock --check` verifies that the lockfile matches the manifest. Virtual environments remain ignored.

This is a non-package uv project (`package = false`): run the existing server file directly. No extra source directories or package entry points are required.

## Contributor workflow

1. Read [Repository Guidelines](../AGENTS.md), the feature's proposal requirements, and applicable safety rules.
2. Resolve blocking choices in the [decision register](decisions.md); record validated versions and procedures here.
3. Keep new source, tests, configuration, and scenarios within their reserved directories.
4. Link tests to feature names/IDs and safety rules. Report results and limitations in the PR.
5. Update documentation to describe actual behavior and reproducible commands as implementation becomes available.

Keep credentials and machine-local connection settings out of version control. The existing `.gitignore` excludes `.env` and virtual environments; it does not provide blanket protection for every local credential directory. Review staged files before committing. Do not include operator credentials or sensitive approval material in examples or logs.
