# Development Setup Template

Status: no application, package manifest, dependency lock, build system, test runner, formatter, or linter exists. Python is the proposal language; exact versions and tools are undecided. Do not present the following placeholders as working commands.

## Environment record to complete

| Item | Required record | Current value |
| --- | --- | --- |
| Host | Supported OS, architecture, resource requirements | TBD |
| Python | Version and environment/package management | TBD |
| MCP | SDK version, transport, client configuration | TBD |
| MAVSDK | Version, backend requirements, connection methods | TBD |
| ArduPilot | SITL and physical firmware versions/configuration | TBD |
| Gazebo | Version, model/world assets, integration dependencies | TBD |
| MAVLink-M | Dialect/version, generation tools, integration mechanism | TBD |
| Quality tooling | Test framework, formatter, lint/type checks, coverage policy | TBD |

## Command inventory to complete after validation

Record the command, working directory, prerequisites, configuration inputs, expected output, and cleanup for each operation:

| Operation | Command |
| --- | --- |
| Install dependencies / reproduce environment | TBD — no manifest exists |
| Start MCP server / connect client | TBD — no entry point or transport selected |
| Start operator interface | TBD — interface technology undecided |
| Run unit and integration tests | TBD — no executable tests |
| Start / stop / reset simulation | TBD — see [simulation template](runbooks/simulation.md) |
| Run safety scenarios and benchmarks | TBD — no runner exists |
| Format, lint, type-check, and build | TBD — no tooling configured |

An optional generic Python environment can be created with `python3 -m venv .venv` and activated in Bash with `source .venv/bin/activate`. This does not install or start MAMBA and is not a validated project setup. `git diff --check` checks whitespace in tracked changes.

## Contributor workflow

1. Read [Repository Guidelines](../AGENTS.md), the feature's proposal requirements, and applicable safety rules.
2. Resolve blocking choices in the [decision register](decisions.md); record validated versions and procedures here.
3. Keep new source, tests, configuration, and scenarios within their reserved directories.
4. Link tests to feature names/IDs and safety rules. Report results and limitations in the PR.
5. Update documentation to describe actual behavior and reproducible commands as implementation becomes available.

Keep credentials and machine-local connection settings out of version control. The existing `.gitignore` excludes `.env` and virtual environments; it does not provide blanket protection for every local credential directory. Review staged files before committing. Do not include operator credentials or sensitive approval material in examples or logs.
