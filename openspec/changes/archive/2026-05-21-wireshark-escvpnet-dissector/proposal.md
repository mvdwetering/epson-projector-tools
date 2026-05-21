## Why

Debugging ESC/VP.net sessions requires packet-level visibility into the binary handshake and subsequent ESC/VP21 command stream. Without a protocol-aware dissector, Wireshark shows raw bytes with no field labelling, making it slow to diagnose handshake failures, authentication issues, or malformed commands.

## What Changes

- **New**: Lua dissector plugin (`escvpnet.lua`) for Wireshark that decodes ESC/VP.net packets on TCP port 3629
- **New**: Dissector parses the 16-byte header fields (magic, version, type, reserved, status, num_headers) for all message types (HELLO, PASSWORD, CONNECT and their responses)
- **New**: After session establishment, subsequent bytes are handed off to the ESC/VP21 data display (shown as raw ASCII command stream)
- **New**: Dissector registers on TCP port 3629 and can be manually applied to any TCP stream

## Capabilities

### New Capabilities
- `escvpnet-wireshark-dissector`: Wireshark Lua dissector that decodes the ESC/VP.net binary protocol, labelling header fields, message types, status codes, and payload contents according to the ESC/VP.net specification

### Modified Capabilities
<!-- No existing specs require changes -->

## Impact

- New standalone file: `dissectors/escvpnet.lua` (no dependency on emulator Python code)
- No changes to existing Python transports, state, or UI
- Requires Wireshark with Lua scripting enabled (standard in most Wireshark builds)
