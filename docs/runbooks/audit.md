# Audit Recording and Review Template

Source: proposal F4 and safety/authorization features. No log writer, schema, storage location, viewer, or retention policy exists yet.

## Required information

The proposal calls for chronological records including, where applicable: timestamp, tool name and arguments, agent/session identity, safety decision, MAVSDK result, vehicle response, and final MCP result. Capture rejected and failed calls as well as successful ones, state transitions, approvals/denials, and manual-override events.

Recommended review metadata includes run/request correlation and target vehicle/payload so concurrent traces can be distinguished. Actual field names, format, persistence, clock policy, redaction, access, and retention remain TBD in the [decision register](../decisions.md). Avoid unnecessarily exposing sensitive authorization information.

## Review procedure to complete

1. Identify the run, revision, environment, and audit source (location/view command TBD).
2. Follow operator/agent request through the target selection, safety decision, adapter/vehicle outcome, and final tool response.
3. Compare ordering, state evidence, authorization and rejection reasons with the scenario's expected results.
4. Correlate state transitions and manual override; distinguish command submission, acknowledgment, and actual completion.
5. Record missing evidence and attach sanitized trace references to the test result or issue.

## Failure behavior to validate

Exercise unavailable destinations and write failures; confirm they are detectable and audit information is not silently discarded. Whether execution must stop, buffer, or use another recovery mechanism is unresolved and requires an explicit decision. Document the chosen behavior and test it before relying on audit evidence.
