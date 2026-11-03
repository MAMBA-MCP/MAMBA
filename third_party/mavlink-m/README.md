# Pinned MAVLink-M schema

`military.xml` is an unmodified snapshot of Dronecode/mavlink-military commit
`23cec36751681aa281c1e5ca6b222a07c6c0c002`, licensed under the adjacent MIT
`LICENSE`. `manifest.json` records original URLs and SHA-256 values. The bytes
were downloaded from the pinned upstream revision and also matched the existing
local reference project. This snapshot is selected for the MAMBA-28/29 experiment;
it is not a claim that this revision is latest or standardized.

The original includes `common.xml`, which is not vendored here. This is not a
standalone full-dialect mavgen input. The experiment uses the installed SDK's
built-in common definitions, and `mamba.participant.participant_xml()` extracts
the exact `PARTICIPANT_POSITION` message and its three enum definitions into a
self-contained fragment for runtime loading and independent binding generation.
No other message has a semantic adapter or transmit path in MAMBA. Generated
pymavlink code stays in the scenario output directory and is not committed.

Do not edit the vendored schema in place. An intentional version change must
update the manifest, application checksum, tests, mapping matrix and wire
acceptance evidence together. The checksum detects drift, not signer identity.
