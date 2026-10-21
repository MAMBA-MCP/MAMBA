# Hardware Validation Runbook Template

Status: incomplete planning template, not an approved operational checklist. Sources: proposal F17 and release-table F19. F19 has no detailed acceptance section; resolve it before claiming hardware acceptance.

## Readiness information required

- Applicable simulation test results, revision, unresolved issues, and documented simulation/hardware differences.
- Approved physical vehicle/payload, firmware versions, connection configuration, identity, and communication hardware.
- Reviewed platform safety configuration and authorized test scope, environment, personnel responsibilities, and approval record.
- Pre-test checks, manual-control/override verification, emergency and communication-loss procedures, and shutdown procedure.
- Validated commands and expected observations for each step (TBD); audit destination and evidence collection procedure.

These records must be completed and reviewed before this template becomes an operating procedure. Operating envelopes, emergency actions, and approval authority must come from the applicable reviewed requirements; this scaffold supplies none.

## Incremental validation sequence

1. Confirm required simulation scenarios passed and complete the reviewed pre-test checklist.
2. Connect the physical vehicle and independently verify its identity before enabling commands.
3. Verify connection status and telemetry-only communication, including an agent-mediated telemetry request.
4. Proceed only to the approved low-risk command within the documented test scope.
5. Verify safety enforcement and manual override using the approved procedure.
6. Preserve audit/results and perform the approved shutdown procedure.

Do not expand the test scope automatically after a successful step. If identity, telemetry, configuration, communications, or control readiness is uncertain, do not progress to state-changing tests; apply the reviewed failure/emergency procedure.

## Evidence and exit record

Record hardware/firmware identifiers, configuration and code revisions, operator/reviewer, approved scope, timestamps, expected/observed results, audit references, exceptions, and shutdown confirmation. Link F17 results to A17 in the [acceptance matrix](../testing/acceptance-matrix.md). Record F19 acceptance as unresolved until stakeholders define it; F17 success alone does not establish F19 completion.
