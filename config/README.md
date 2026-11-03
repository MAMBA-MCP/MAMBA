# Configuration Definitions

For MAMBA-2 / F2 connection discovery, select `vehicle.example.toml` explicitly with `--config` or supply a local copy. It defines one MAVLink endpoint and expected system ID. See the [connection schema and runbook](../docs/runbooks/connection.md). The example is not loaded automatically and has not been validated against SITL or hardware.

[vehicles/](vehicles/) and [payloads/](payloads/) reserve space for reviewed, versioned operating-envelope and state-machine definitions. Vehicle/payload safety definitions, valid transition models, and operational thresholds are not defined yet; the connection TOML is separate from those future definitions.

Use customer/SME-validated requirements; document states, telemetry evidence, transitions, constraints, authorization, host dependencies, and tests as described in [safety requirements](../docs/safety.md). Keep credentials and machine-local connection settings outside versioned platform definitions. Do not add speculative executable examples.
