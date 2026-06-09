## Context

The ESC/VP21 engine is the single command parser/formatter used by all emulator transports. Current behavior emits `\r:` for successful SET acknowledgments and null-command acknowledgments, while real projectors emit only `:` for these cases. This mismatch can break strict protocol clients and causes emulator behavior to diverge from hardware expectations.

## Goals / Non-Goals

**Goals:**
- Ensure null command acknowledgments are emitted as `:`.
- Ensure successful SET acknowledgments are emitted as `:`.
- Preserve existing query response shape and existing error framing unless explicitly changed by requirement updates.
- Validate behavior with tests at engine and transport-observable boundaries.

**Non-Goals:**
- Changing query result format (for example `CMD=value\r:` behavior).
- Changing error response format (for example `ERR\r:`).
- Refactoring transport implementations beyond what is required to consume updated engine output.

## Decisions

- Decision: Implement acknowledgment framing change at the engine response-construction point.
  - Rationale: Engine is the protocol authority used by serial, VP.net, and HTTP handlers. A single engine-level fix guarantees consistent behavior across all transports.
  - Alternative considered: Patch each transport to strip `\r` for specific commands. Rejected because it duplicates protocol logic and risks divergence.

- Decision: Treat plain carriage-return input as a dedicated null-command path that returns `:`.
  - Rationale: This preserves clear semantics and avoids relying on side effects in generic parsing branches.
  - Alternative considered: Normalize blank commands to an existing command branch. Rejected because it can unintentionally affect validation paths.

- Decision: Update and add tests for null and successful SET acknowledgments where observable.
  - Rationale: Prevent regressions and encode projector-accurate behavior as executable specification.
  - Alternative considered: Manual verification only. Rejected due to recurring risk in protocol framing.

## Risks / Trade-offs

- Risk: Existing tests may rely on legacy `\r:` acknowledgment framing. → Mitigation: Update assertions to match new requirement and keep unaffected query/error tests unchanged.
- Risk: Hidden callers may assume acknowledgments always include `\r`. → Mitigation: Constrain changes to null/successful SET paths and verify transport-level behavior in current test suite.
- Trade-off: Different framing conventions remain (`:` for ack vs `\r:` for query/error), which increases protocol nuance. → Mitigation: Capture this explicitly in modified spec scenarios and tests.

## Migration Plan

1. Update spec delta for `escvp21-engine` to define colon-only acknowledgments for null and successful SET behavior.
2. Modify engine response construction for null and successful SET command paths.
3. Update tests asserting old `\r:` acknowledgments to assert `:`.
4. Run targeted tests for engine and transports.
5. If regressions appear in dependent clients, rollback by reverting the engine framing change and updated assertions.

## Open Questions

- Should any additional success-only commands beyond SET share the colon-only acknowledgment requirement, or remain unchanged?
