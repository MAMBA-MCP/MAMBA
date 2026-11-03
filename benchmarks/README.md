# Benchmarking

[Telemetry interface comparison](telemetry-interface.md) records descriptor and representative response sizes for the individual and consolidated telemetry tools. Reproduce it with `uv run --locked python benchmarks/measure_telemetry_interface.py /tmp/mamba-interface-size.json` from the repository root. This static measurement does not connect to a vehicle or measure model token use, tool-selection accuracy, or flight performance.

[scenarios/](scenarios/) reserves repeatable workload definitions; [reports/](reports/) reserves reviewed summaries and references to collected evidence. Safety, mission, and agent-performance benchmark runners remain planned.

Measure safety decisions/reasons, latency, sequence and transition correctness, agent response to rejection, and tool-selection effectiveness as described in the [testing plan](../docs/testing/README.md). Document workload, versions, measurement boundaries, sample counts, units, and limitations. Storage/retention and publication of raw traces remain TBD; do not commit credentials, sensitive authorization material, or unreviewed operational logs.
