# Simulation Runbook Template

Status: not executable. Gazebo, ArduPilot SITL, MAVSDK, MCP integration, scenarios, and startup scripts are not installed or implemented by this scaffold. Sources: proposal F5, F6, F14, F16, and F20.

## Required environment record

Before use, record OS/resources, exact dependency and firmware versions, world/model assets, vehicle identifiers, endpoints/ports, configuration revision, expected initial states, MCP client/agent configuration, audit destination, and known limitations. Commands and paths for those inputs are TBD.

## Startup sequence to validate

1. Confirm isolated simulation endpoints and available ports; select a documented scenario and reset state.
2. Start Gazebo and ArduPilot SITL using validated commands (TBD); verify the expected model and vehicle identity.
3. Start MAMBA (TBD), verify MAVSDK connectivity and current telemetry, then connect the MCP client/agent (TBD).
4. Verify tool discovery and telemetry-only requests before simulated state-changing actions.
5. Run the selected acceptance/safety scenario using its future runner (TBD); capture results and audit evidence.

For payload scenarios, record simulated capabilities, dialect/version, target component and fault injection. For multi-UAS scenarios, start at least two independent SITL instances with distinct endpoints/identities and verify independent telemetry before commands.

## Failure handling to document and validate

Cover Gazebo/SITL startup failure, port conflict, missing/stale telemetry, MAVSDK connection failure, simulator termination, payload unavailability, and vehicle disconnection. Record diagnostics and observed safety decisions; do not infer readiness from a visible model alone.

## Shutdown and reset sequence to validate

Stop scenario requests, conclude the simulated operation, preserve evidence, disconnect the client, and stop MAMBA/SITL/Gazebo with validated commands (all TBD). Document how queued commands, pending approvals, and old state are cleared or invalidated before rerun. Restore the scenario's initial conditions and verify fresh identities/telemetry. Record whether repeating the same scenario reproduces results.

Do not reuse simulation endpoints or procedures as a physical-hardware procedure. Use the separate [hardware template](hardware.md) after applicable simulation validation.
