# Future Tests

Run `uv run --locked pytest -q`. `unit/test_vehicle_connection.py` covers F2/A02 using a controlled MAVSDK substitute; `integration/test_stdio.py` covers F1/A01 and F2/A02 through stdio and native empty-endpoint timeout. ArduPilot SITL and hardware acceptance remain pending. Test levels are [unit/](unit/), [integration/](integration/), [simulation/](simulation/), and [hardware/](hardware/). pytest is configured in `pyproject.toml`; coverage policy remains TBD.

Follow the [testing plan](../docs/testing/README.md), map future tests to [acceptance scenarios](../docs/testing/acceptance-matrix.md) and [safety rules](../docs/testing/safety-matrix.md), and document commands once implemented. Hardware tests must remain explicit, controlled procedures after applicable simulation validation; no hardware runner or automatic execution is established here.
