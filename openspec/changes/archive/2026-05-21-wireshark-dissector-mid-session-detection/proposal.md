## Why

When Wireshark is started after the ESC/VP.net handshake (CONNECT exchange) has already completed, the dissector has no record of the phase transition and defaults to "handshake" mode. Every subsequent ESC/VP21 command packet is then labelled `[Unknown / non-ESC/VP.net data]` instead of being decoded as ESC/VP21 traffic.

## What Changes

- The dissector gains a heuristic: if a packet arrives in "handshake" phase but its payload matches the ESC/VP21 text command pattern (`CMD?` or `CMD VALUE\r`), the stream is promoted to "data" phase immediately and the packet is decoded as ESC/VP21 data.
- The info column for such packets will indicate that the phase was inferred (e.g. `ESC/VP21 data [session inferred]`) so analysts know the handshake was not captured.

## Capabilities

### New Capabilities

- `escvpnet-wireshark-dissector`: Update the Lua dissector to heuristically detect mid-session ESC/VP21 traffic and decode it correctly when the handshake was not captured.

### Modified Capabilities

<!-- No existing spec-level requirements are changing -->

## Impact

- `dissectors/escvpnet.lua` — add heuristic detection in the handshake branch of `escvpnet_proto.dissector`.
- No Python code, no model YAML, no transport code is affected.
- Purely a Lua file change; no new dependencies.
