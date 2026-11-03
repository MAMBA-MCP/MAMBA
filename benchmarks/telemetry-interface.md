# Telemetry interface size comparison

Measured on 2026-11-03 with Python 3.14.4, FastMCP 2.14.7, and MAVSDK 4.0.6. The baseline is commit `ad43579` (five individual telemetry tools); the comparison is the consolidated interface on `feature/mamba-26-27-vehicle-data`.

| Measurement | Individual tools | Consolidated tool |
| --- | ---: | ---: |
| Catalog tool count | 8 | 4 |
| Complete catalog descriptors, bytes | 7505 | 6888 |
| Telemetry descriptors only, bytes | 4392 | 3775 |
| Position response payload, bytes | 162 | 200 |
| Position + battery + health response payloads, bytes | 694 | 725 |

The catalog is 617 bytes smaller (8.2%). Telemetry descriptors are 14.0% smaller. The example response payloads grow by 38 and 31 bytes because the batch adds category labels and partial-error metadata. Retrieving three categories now uses one call; the baseline response measurement sums three individual payloads. These are byte counts, not model token counts or evidence of improved agent reliability.

## Reproduction and boundaries

Run from the repository root:

```bash
uv run --locked python benchmarks/measure_telemetry_interface.py /tmp/mamba-interface-size.json
```

The script imports `src` from the working directory, creates the server without entering its connection lifespan, and measures its sorted MCP tool descriptors. It serializes JSON with sorted keys, compact separators, UTF-8 encoding, and no ASCII escaping. Descriptor dumps omit null-valued metadata. Response samples use fixed position, battery, health, system ID, and receipt timestamp values defined in the script; unknown measurements remain null.

To repeat the baseline, invoke this script by absolute path while working in a separate checkout of `ad43579`. It detects the available interface. No vehicle, network connection, model call, or flight operation is performed. Payload measurements exclude MCP transport envelopes, tool-call arguments, message history, and any duplicated text/structured representation. Actual context usage depends on the client and tokenizer.
