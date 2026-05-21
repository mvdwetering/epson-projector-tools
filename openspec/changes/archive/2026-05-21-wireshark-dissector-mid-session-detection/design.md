## Context

The ESC/VP.net dissector (`dissectors/escvpnet.lua`) tracks per-stream state in the `stream_phases` table, keyed by `tostring(pinfo.conversation)`. A stream starts in `"handshake"` phase and transitions to `"data"` phase only when a CONNECT response (type=0x03, status=0x20) is observed. When Wireshark starts capturing after this response has already passed, the table entry is never written, the stream stays in `"handshake"` phase forever, and ESC/VP21 command packets are rejected with `[Unknown / non-ESC/VP.net data]`.

## Goals / Non-Goals

**Goals:**
- Detect ESC/VP21 command traffic arriving in handshake phase and automatically promote the stream to data phase.
- Label such packets distinctively so analysts know the handshake was not captured.
- Leave all existing behavior unchanged for captures that include the full handshake.

**Non-Goals:**
- Reconstructing or back-filling the handshake information.
- Handling fragmented/reassembled TCP segments — Wireshark PDU reassembly is already handled by the existing stream.
- Any changes to Python emulator code or model YAML files.

## Decisions

### Heuristic pattern for ESC/VP21 detection

**Decision**: Match the payload against a Lua pattern that covers the two ESC/VP21 request forms:
- Query: `CMD?` followed by `\r` (carriage return, ASCII 0x0D)
- Set/action: `CMD VALUE\r` (one uppercase-letter token, space, value token, `\r`)
- Response: `CMD=VALUE\r` (projector replies use `=`)

Pattern: `^[A-Z][A-Z0-9 ]*[?=]?[^\r]*\r` — requires the payload to start with an uppercase ASCII letter, contain only printable ASCII, and end with `\r`.

**Alternative considered**: Check only for the `\r` terminator. Rejected — too loose; binary handshake garbage would occasionally match.

**Alternative considered**: Check for specific known commands. Rejected — fragile across model variants; the general pattern is sufficient and future-proof.

### Phase promotion scope

**Decision**: Promote the stream on the *first* matching packet and retain `"data"` phase for all subsequent packets in the conversation. This mirrors what happens after a captured CONNECT response.

### Info-column annotation

**Decision**: Append ` [session inferred]` to the info column for the first packet that triggers promotion. Subsequent packets in the same conversation get the normal `ESC/VP21 data` label. This tells analysts exactly one packet was the inference point without cluttering every row.

**Alternative considered**: Annotate all inferred-phase packets. Rejected — noisy; the first marker is sufficient.

## Risks / Trade-offs

- **False positive on non-ESC/VP.net TCP port 3629 traffic**: A third-party application using the same port with ASCII data starting with uppercase letters and ending in `\r` would be mis-decoded. Mitigation: The pattern is deliberately restrictive (uppercase start, only printable ASCII, `\r` terminator); real-world risk is negligible on a projector control port.
- **Wireshark re-dissection**: The `stream_phases` table lives for the lifetime of the Lua plugin. If the user forces re-dissection (`Ctrl+Shift+R`), the table may have stale entries. This is the same limitation as the existing phase-tracking code and is not introduced by this change.
