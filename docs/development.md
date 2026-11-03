# Development Setup

Status: the MCP server entrypoint is `src/mamba/server.py`, with connection configuration, discovery, status types, and SDK lifecycle in `src/mamba/connection.py`, using FastMCP 2 and stdio transport. It exposes `ping`, returning `pong`, and read-only `get_vehicle_status`. uv manages dependencies in `pyproject.toml`, resolved versions in `uv.lock`, and the local `.venv`. Optional `--config` startup TOML enables persistent native `mavsdk.asyncio` discovery for one configured system ID (MAMBA-2 / F2). pytest covers configuration, lifecycle, and stdio integration. No vehicle commands, safety enforcement, package build, formatter, or linter exists. ArduPilot SITL acceptance remains pending. Remaining TBD commands are planning placeholders.

## Environment record to complete

| Item | Required record | Current value |
| --- | --- | --- |
| Host | Supported OS, architecture, resource requirements | TBD |
| Python | Version and environment/package management | Python 3.11+; uv-managed `.venv` |
| MCP | SDK version, transport, client configuration | FastMCP 2 (`fastmcp>=2,<3`), stdio; client launch below |
| MAVSDK | Version, backend requirements, connection methods | `mavsdk>=4.0.6,<5`; native asyncio binding; exact version in `uv.lock`; ArduPilot validation pending |
| ArduPilot | SITL and physical firmware versions/configuration | TBD |
| Gazebo | Version, model/world assets, integration dependencies | TBD |
| MAVLink-M | Dialect/version, generation tools, integration mechanism | TBD |
| Quality tooling | Test framework, formatter, lint/type checks, coverage policy | pytest (dev dependency); other tooling/coverage TBD |

## Command inventory to complete after validation

Record the command, working directory, prerequisites, configuration inputs, expected output, and cleanup for each operation:

| Operation | Command |
| --- | --- |
| Install dependencies | `uv sync --locked` from repository root |
| Start MCP server | `uv run --locked python src/mamba/server.py` from repository root; stdio client required |
| Start operator interface | TBD — interface technology undecided |
| Run unit and integration tests | `uv run --locked pytest -q` from repository root; no vehicle required |
| Start / stop / reset simulation | TBD — see [simulation template](runbooks/simulation.md) |
| Run safety scenarios and benchmarks | TBD — no runner exists |
| Format, lint, type-check, and build | TBD — no tooling configured |

## Run the basic server

```bash
uv sync --locked
uv run --locked python src/mamba/server.py
```

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and use Python 3.11+ for [FastMCP 2](https://gofastmcp.com/). The process waits for MCP messages on stdin; stdout carries protocol traffic. A client can launch `uv` with arguments `run --locked --project /absolute/path/to/MAMBA python /absolute/path/to/MAMBA/src/mamba/server.py`; use the absolute uv executable path if the client does not inherit your shell PATH. No HTTP endpoint is exposed. Without configuration, vehicle status is `unconfigured`. For discovery, append `--config /absolute/path/to/vehicle.toml`; see the [connection runbook](runbooks/connection.md) for schema, identity selection, failure/recovery, and SITL/physical setup examples. Call `ping` with `{}` to receive `pong`. Stop a manually launched process with Ctrl+C; a client manages its subprocess lifecycle.

Keep protocol stdout free of diagnostic prints. Exact dependency versions are recorded in `uv.lock`. `git diff --check` checks whitespace in tracked changes.

Validated on 2026-10-26: `uv sync --locked` succeeded with FastMCP 2.14.7. Stdio tests initialize sessions, discover `ping` and `get_vehicle_status`, and verify `ping` returns `pong` with absent, missing, and invalid configuration. A real MAVSDK 4.0.6 loopback UDP listener times out without stopping MCP; substitute-based tests cover matching IDs, persistent transport, disconnect, and recovery. Successful ArduPilot SITL discovery and physical acceptance have not been run. The final validation used Python 3.14.4 on Linux: `uv sync --locked` succeeded and `.venv/bin/python -m pytest -q` reported **28 passed in 18.81s**, with two upstream Authlib deprecation warnings. Native networking/executor checks required execution outside the restricted agent sandbox. `git diff --check` passed. Dependency deprecation warnings appeared on stderr without disrupting protocol traffic.


## Connection module refactor validation

On 2026-11-03, `.venv/bin/python -m pytest -q tests/unit/test_vehicle_connection.py -k 'invalid_config or valid_config or unconfigured'` passed 19 tests (5 deselected). Syntax checks, package imports (`mamba.server` / `mamba.connection`), sibling imports for direct script execution, and FastMCP server creation also passed. `git diff --check` passed. The full `uv run --locked pytest -q` suite could not run in the restricted environment, and execution outside that environment was not approved; the prior full-suite results above predate this refactor. Stdio/native connection tests and SITL acceptance have not been rerun for this split.

## Dependency workflow

Use `uv add <dependency>` (or `uv add --dev <dependency>` for development tools) and `uv remove <dependency>` to change requirements. Use `uv lock --upgrade-package <dependency>` for an intentional upgrade, then `uv sync --locked`. Commit `pyproject.toml` and `uv.lock` together. `uv lock --check` verifies that the lockfile matches the manifest. Virtual environments remain ignored.

This is a non-package uv project (`package = false`): run the existing server file directly. No extra source directories or package entry points are required.

## Contributor workflow

1. Read [Repository Guidelines](../AGENTS.md), the feature's proposal requirements, and applicable safety rules.
2. Resolve blocking choices in the [decision register](decisions.md); record validated versions and procedures here.
3. Keep new source, tests, configuration, and scenarios within their reserved directories.
4. Link tests to feature names/IDs and safety rules. Report results and limitations in the PR.
5. Update documentation to describe actual behavior and reproducible commands as implementation becomes available.

Keep credentials and machine-local connection settings out of version control. The existing `.gitignore` excludes `.env` and virtual environments; it does not provide blanket protection for every local credential directory. Review staged files before committing. Do not include operator credentials or sensitive approval material in examples or logs.
