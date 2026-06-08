## Context

Model data is now produced as JSON extracted from Epson-provided workbooks. The JSON schema contains command rows plus metadata (`sources`, `irCodes`, connectivity flags), while current emulator behavior assumes a compact YAML command map and startup-only model selection.

This change introduces a JSON-first runtime model without broad protocol rewrites. It prioritizes correctness for common single-parameter commands and intentionally defers complex multi-parameter command semantics.

## Goals / Non-Goals

**Goals:**
- Use JSON as the only supported model input format.
- Keep command behavior model-driven, including SOURCELIST/SOURCELISTA and KEY validation.
- Implement runtime model switching from TUI using a restart sequence for safety.
- Improve TUI state table usability for large model command sets.
- Keep transport support differences visible in UI without blocking listener behavior.

**Non-Goals:**
- Perfect parameter-level emulation for every multi-parameter command in this pass (for example, full GRAYSCALE semantics).
- Dynamic transport enable/disable based on model connectivity.
- Expanding protocol box layout with additional rows for warnings.

## Decisions

1. JSON-only model format
- Decision: Remove YAML model loading support from startup and model parser path.
- Rationale: model source-of-truth is workbook-derived JSON and avoiding dual formats prevents drift.
- Trade-off: existing YAML-only custom models must be converted.

2. Effective command aggregation from JSON rows
- Decision: Aggregate multiple JSON command rows by command token into one effective runtime command definition.
- Rationale: workbook exports represent functions per row, but engine logic requires per-token capability.
- Notes: readable/writable come from any matching row; accepted set values come from parsed command constraints.

3. SOURCELIST and SOURCELISTA behavior
- Decision: Return the same source payload for both commands for now.
- Rationale: exact behavioral difference is unclear; same payload keeps integration stable.
- Payload format: `CMD=<code1> <name1> <code2> <name2> ...` with non-cyclic sources only.
- SOURCE validation: `SOURCE <code>` operands are validated against the same non-cyclic model source code list used for both source-list responses.

4. KEY operand validation source
- Decision: validate `KEY` operands against `irCodes`.
- Rationale: requested behavior and closest mapping to remote key code execution.

5. INC/DEC restrictions for this milestone
- Decision: allow INC/DEC only for commands that are both:
  - marked INC/DEC-capable by model data,
  - single-parameter decimal adjustment commands.
- Rationale: avoids incorrect behavior on mixed/complex commands and matches observed data for standard commands like `VOL`.
- Consequence: complex commands such as `GRAYSCALE` return ERR for INC/DEC in this pass.

6. Runtime model switch via safe restart
- Decision: model switch from UI performs internal restart sequence: stop transports, load model/state, rebuild UI tables, restart transports.
- Rationale: safer than hot-swapping model under active sessions.

7. Transport support indication
- Decision: show unsupported indicators inline on each transport line in config panel; do not add extra rows.
- Rationale: preserves compact layout while surfacing model capability hints.
- Interpretation of unknown connectivity (`null`): assume supported and do not flag as unsupported.

8. State ordering model
- Decision: state table order is pinned-first, then up to 6 recent active commands, then alphabetical remainder.
- Rationale: keeps high-signal commands visible and still deterministic.

## Risks / Trade-offs

- [Risk] JSON schema may evolve slightly over time. -> Mitigation: isolate parsing logic and fail with descriptive errors for missing critical fields.
- [Risk] Aggregation could misinterpret edge-case command rows. -> Mitigation: start with conservative behavior and targeted tests for common commands.
- [Risk] Restart-on-switch interrupts active sessions. -> Mitigation: explicit restart semantics; no hidden partial hot-swap behavior.
- [Risk] SOURCELIST/A parity may not match every device. -> Mitigation: document as temporary compatibility behavior.

## Migration Plan

1. Implement JSON loader and runtime command aggregation.
2. Update startup model resolution to JSON-only.
3. Add engine behavior for SOURCELIST/SOURCELISTA payload and KEY IR validation.
4. Add SOURCE operand validation using model sources.
5. Apply INC/DEC decimal single-parameter guardrails.
6. Add TUI model picker and restart flow.
7. Update state ordering and inline transport support markers.
8. Add regression tests for common commands and new UI ordering behavior.

Rollback:
- Revert to prior model loader and TUI behavior in one change set; transport implementations remain unchanged.

## Open Questions

- Whether SOURCELIST and SOURCELISTA should diverge in a future change once behavior is clarified.
- Whether model title should prefer filename or model name by default when both are available (both acceptable in this change scope).
- Whether command metadata should eventually include explicit per-parameter numeric base instead of inferring from lexical form.