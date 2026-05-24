## Context

The ESC/VP.net dissector currently keeps per-conversation phase state (`handshake` vs `data`) and also includes a mid-session ESC/VP21 heuristic when magic is absent. In practice, each ESC/VP.net packet is self-identifying via the `ESC/VP.net` magic prefix, so stream-level mode tracking is unnecessary for deciding how to decode an individual packet.

## Goals / Non-Goals

**Goals:**
- Replace stateful stream phase logic with packet-local dispatch.
- Decode packets with `ESC/VP.net` magic as ESC/VP.net binary messages.
- Decode packets without magic as ESC/VP21 payload data.
- Preserve validation behavior for true ESC/VP.net packets (version/reserved/length checks).

**Non-Goals:**
- Changing ESC/VP.net field definitions or extension-header parsing.
- Introducing reassembly or multi-packet ESC/VP21 parsing.
- Modifying emulator transports or ESC/VP21 engine behavior.

## Decisions

1. Use magic-prefix dispatch as the primary classifier.
- Decision: Replace stream phase tracking with a single check per packet: `tvb(0, MAGIC_LEN) == MAGIC`.
- Rationale: The protocol already defines a unique magic marker for ESC/VP.net headers, making prior packet history unnecessary.
- Alternative considered: Keep phase tracking and only simplify heuristic thresholds. Rejected because it still relies on mutable conversation state and can drift across reconnects.

2. Remove conversation-state tables and inferred-session labels.
- Decision: Delete `stream_phases` and `inferred_frames` state and associated transition logic.
- Rationale: Stateless classification avoids incorrect mode carryover across reused conversation keys and makes behavior deterministic from packet bytes alone.
- Alternative considered: Keep state only as an optimization. Rejected because the complexity outweighs any negligible performance benefit.

3. Treat non-magic payloads as ESC/VP21 data directly.
- Decision: For packets that do not start with magic, render payload under `escvp21_data` and set info column to `ESC/VP21 data`.
- Rationale: This matches observed traffic patterns and user intent for mid-session captures without fragile heuristics.
- Alternative considered: Continue labeling unknown non-magic payloads as unknown. Rejected because users expect readable ESC/VP21 payloads in post-handshake captures.

## Risks / Trade-offs

- [Risk] Binary non-ESC/VP.net payloads on port 3629 could be shown as ESC/VP21 data.
  → Mitigation: Keep labeling explicit as `ESC/VP21 data`; if needed later, add an optional strict mode.
- [Risk] Existing users may rely on inferred-session annotation text.
  → Mitigation: Note behavior change in change summary and keep protocol/details tree consistent.
- [Trade-off] Loss of explicit handshake completion semantics in the dissector internals.
  → Mitigation: Handshake packets remain fully decoded whenever magic is present.

## Migration Plan

- Update `dissectors/escvpnet.lua` to remove stateful mode code paths.
- Verify with captures containing handshake packets and mid-session ESC/VP21 payloads.
- Rollback strategy: Revert the dissector file to previous logic if decoding regressions are found.

## Open Questions

- Do we want an optional expert note when non-magic payload contains non-printable bytes but is still shown as ESC/VP21 data?
