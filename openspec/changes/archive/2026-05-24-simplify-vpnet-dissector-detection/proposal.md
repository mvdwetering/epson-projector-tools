## Why

The current dissector keeps per-stream mode state and a heuristic to infer ESC/VP21 text mode, but ESC/VP.net packets are already self-identifying by the `ESC/VP.net` magic prefix. This stateful behavior adds complexity and can misclassify packets when simple magic-based dispatch is sufficient.

## What Changes

- Simplify decoding logic to use packet-local classification only:
- If payload starts with `ESC/VP.net`, decode as ESC/VP.net header and extension headers.
- Otherwise, decode as plain ESC/VP21 text payload.
- Remove per-conversation phase tracking (`handshake` vs `data`) and inferred-session annotations.
- Remove the mid-session ESC/VP21 heuristic and any promotion logic tied to CONNECT responses.
- Keep protocol validation and expert info for malformed ESC/VP.net packets that do contain the magic prefix.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `escvpnet-wireshark-dissector`: Replace stateful handshake/data mode tracking with stateless magic-prefix dispatch (`ESC/VP.net` => VP.net decode, otherwise ESC/VP21 decode).

## Impact

- Affected code: `dissectors/escvpnet.lua` packet classification and info-column labeling paths.
- Affected behavior: packet decoding becomes deterministic per packet and independent of prior packets on the stream.
- API/dependency impact: none; still a single Wireshark Lua plugin with no external dependencies.
