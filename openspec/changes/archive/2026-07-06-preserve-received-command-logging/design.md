## Context

`HttpTransport._dispatch_key` currently executes mapped IR keys by translating them into internal VP21 commands (for example `KEY=40` -> `SOURCE A0`) and logging that translated command via `_exec`. The resulting command log no longer reflects what arrived over HTTP. Operators expect logs to show ingress commands exactly as received, while state transitions should continue to follow existing mappings.

Key dispatch is also transport-local today because this behavior lives in `transports/http.py`. Commands arriving over serial TCP and ESC/VP.net already flow through shared `handle_command`, but do not benefit from the same mapped KEY effects. This causes behavior differences by connection type.

## Goals / Non-Goals

**Goals:**
- Preserve received-command fidelity in logs for all `KEY=<ir_code>` requests.
- Make KEY dispatch behavior transport-independent across HTTP, serial TCP, and ESC/VP.net.
- Preserve existing source-selection KEY behavior (no additional source mappings).
- Add mapped KEY behavior for `VOL INC` and `VOL DEC`.
- Keep observer/logging success-failure semantics aligned with actual execution result.

**Non-Goals:**
- Adding new source-selection mappings beyond current behavior.
- Redesigning command logging APIs across all transports.
- Altering non-KEY `directsend` logging behavior.

## Decisions

- Move KEY dispatch semantics into shared engine handling so all transports inherit the same behavior when they call `handle_command`.
  - Rationale: serial and ESC/VP.net already funnel commands through shared engine code, so engine-level dispatch ensures consistent behavior independent of ingress protocol.
  - Alternative considered: duplicating HTTP dispatch logic in each transport. Rejected due to duplication and drift risk.
- Keep transports logging the original received command string while allowing engine-internal side effects for mapped keys.
  - Rationale: preserves ingress fidelity in logs without observer API changes.
  - Alternative considered: adding separate received/executed fields to command observer payloads. Rejected for larger API churn.
- Add shared KEY mappings for `VOL INC` and `VOL DEC`.
  - Rationale: requested projector behavior should work independent of connection type.
- Keep current source KEY mappings unchanged.
  - Rationale: explicitly requested to avoid additional source mapping expansion.

## Risks / Trade-offs

- [Risk] Logging only the received key may obscure the internal mapped command during debugging. -> Mitigation: keep key mapping table explicit in code/docs and add tests that assert mapped side effects.
- [Risk] Partial refactor may leave some mapped behavior HTTP-only. -> Mitigation: add cross-transport tests for identical `KEY` outcomes via HTTP, serial, and ESC/VP.net paths.
- [Risk] Some models may not support `VOL` inc/dec semantics via current command metadata. -> Mitigation: validate behavior against model command capabilities and fail with standard `ERR\r:` when unsupported.
