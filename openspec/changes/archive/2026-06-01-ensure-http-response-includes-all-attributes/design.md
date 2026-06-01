## Context

The emulator's `json_query` response currently has inconsistent JSON shape across code paths. Some responses include only partial fields, especially when command parsing or execution errors occur. Epson-compatible clients often deserialize a fixed object shape and rely on all fields (`name`, `query`, `reply`, `error`) being present.

## Goals / Non-Goals

**Goals:**
- Define one canonical JSON response builder for `json_query`.
- Ensure success and error responses always include `projector.feature.name`, `query`, `reply`, and `error`.
- Keep existing command semantics intact (`reply` values and error meaning).
- Add regression tests for both successful and malformed query scenarios.

**Non-Goals:**
- Changing endpoint URLs or request parameter names.
- Altering Digest auth behavior.
- Changing directsend response body semantics.

## Decisions

1. Use a single response-construction path for `json_query`.
- Rationale: A single builder prevents field drift between success and error branches.
- Alternative considered: Patch each error path individually. Rejected because it is fragile and likely to regress.

2. Preserve Epson-style fields in all outcomes.
- Rationale: External compatibility depends on stable keys, even when `error=true`.
- Alternative considered: Return HTTP-only error objects for malformed input. Rejected due to client incompatibility risk.

3. Keep HTTP status behavior unchanged unless already inconsistent with current tests.
- Rationale: This change targets payload shape consistency, not transport-layer policy changes.
- Alternative considered: Normalize all failures to one HTTP status. Rejected as out of scope for this change.

4. Add explicit tests for required field presence.
- Rationale: Shape regressions are easy to reintroduce without dedicated assertions.
- Alternative considered: Rely on integration/manual checks. Rejected due to weak regression detection.

## Risks / Trade-offs

- [Risk] Existing clients may depend on a previously omitted field in edge cases being absent. -> Mitigation: Maintain values and semantics, only guarantee field presence.
- [Risk] Refactoring response flow may unintentionally alter status codes. -> Mitigation: Preserve current status behavior and assert only payload shape for this change.
- [Risk] Future endpoint variants (`/cgi-bin/Remote/...`) may diverge again. -> Mitigation: Reuse the same response helper where query semantics are identical.

## Migration Plan

- Implement response-builder refactor in HTTP transport.
- Add/update tests covering success and malformed command responses.
- Validate tests and manual sample responses match expected Epson shape.
- Rollback strategy: revert the response-builder changes if unexpected client behavior appears.

## Open Questions

- Should unknown command handling continue to map to the current HTTP status while still returning full Epson-shaped JSON, or should status normalization be addressed in a follow-up?
