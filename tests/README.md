# Future Tests

No executable tests exist. Reserved levels are [unit/](unit/), [integration/](integration/), [simulation/](simulation/), and [hardware/](hardware/). Framework and coverage policy are TBD; pytest and `test_*.py` are recommendations only.

Follow the [testing plan](../docs/testing/README.md), map future tests to [acceptance scenarios](../docs/testing/acceptance-matrix.md) and [safety rules](../docs/testing/safety-matrix.md), and document commands once implemented. Hardware tests must remain explicit, controlled procedures after applicable simulation validation; no hardware runner or automatic execution is established here.
