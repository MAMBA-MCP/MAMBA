# Future Tests

Run `uv run --locked pytest -q`. `unit/test_vehicle_connection.py` covers F2/A02 using a controlled MAVSDK substitute; `integration/test_stdio.py` covers F1/A01 and F2/A02 through stdio and native empty-endpoint timeout. `unit/test_vehicle_data.py`, `unit/test_telemetry_batch.py`, and `integration/test_vehicle_tools.py` cover MAMBA-26/27 information/telemetry, typed MCP results, errors, session isolation, and cleanup. ArduPilot SITL and hardware acceptance remain pending. Test levels are [unit/](unit/), [integration/](integration/), [simulation/](simulation/), and [hardware/](hardware/). pytest is configured in `pyproject.toml`; coverage policy remains TBD.

Follow the [testing plan](../docs/testing/README.md), map future tests to [acceptance scenarios](../docs/testing/acceptance-matrix.md) and [safety rules](../docs/testing/safety-matrix.md), and document commands once implemented. Hardware tests must remain explicit, controlled procedures after applicable simulation validation; no hardware runner or automatic execution is established here.

## Opt-in native SITL acceptance

`simulation/validate_read_only.py` launches an already-built ArduCopter binary,
connects a real stdio MCP client, compares telemetry with independent MAVLink
observations, and exercises stream loss, cancellation and reconnect. It is
deliberately outside default pytest collection. Install the locked `simulation`
group and follow the [WSL acceptance runbook](../docs/testing/mamba-26-27-sitl.md).
