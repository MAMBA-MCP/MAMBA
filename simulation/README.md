# Future Simulation Assets

[scenarios/](scenarios/) reserves repeatable Gazebo/ArduPilot SITL workflows and fault scenarios. [models/](models/) reserves world/vehicle/payload assets or documented references once dependencies and licensing are verified. A standalone read-only ArduCopter launcher/acceptance harness now lives in [tests/simulation/validate_read_only.py](../tests/simulation/validate_read_only.py); Gazebo assets remain planned. See the [validated WSL workflow](../docs/testing/mamba-26-27-sitl.md).

For each scenario record feature and safety IDs, versions, initial state, identities/endpoints, steps, expected results, fault injection, reset/shutdown, and limitations. Keep executable test assertions in [tests/simulation/](../tests/simulation/). Use the [simulation runbook template](../docs/runbooks/simulation.md) to document actual validated operations.

The [MAVLink-M scenario](../tests/simulation/validate_mavlink_m.py) separately
validates custom XML loading and own-position wire reporting with isolated SITL
telemetry and an independent local peer. See [reproduction and scope](../docs/runbooks/mavlink-m.md).
