## 1. Heuristic Detection Logic

- [x] 1.1 Add a Lua helper function `is_escvp21_payload(tvb)` that returns `true` when the buffer matches the ESC/VP21 pattern (`^[A-Z][A-Z0-9 ]*[?= ][^\r]*\r` or simply starts with uppercase ASCII and ends with `\r`)
- [x] 1.2 Verify the helper correctly matches `PWR?\r`, `PWR ON\r`, and `PWR=01\r`
- [x] 1.3 Verify the helper does not match binary handshake data or payloads without a trailing `\r`

## 2. Dissector Integration

- [x] 2.1 In the handshake branch of `escvpnet_proto.dissector`, after `parse_header` returns `nil` (magic not present), call `is_escvp21_payload` on the payload
- [x] 2.2 If the heuristic matches, promote `stream_phases[conv_key]` to `"data"`, decode the packet as ESC/VP21 data using the existing data-phase code path, and set the info column to `ESC/VP21 data [session inferred]`
- [x] 2.3 Ensure subsequent packets on the same stream use the normal `ESC/VP21 data` label (no `[session inferred]` suffix)

## 3. Verification

- [x] 3.1 Open Wireshark and apply the updated dissector to a live or recorded capture of port 3629
- [x] 3.2 Confirm that a capture started mid-session shows ESC/VP21 commands decoded correctly instead of `[Unknown / non-ESC/VP.net data]`
- [x] 3.3 Confirm that a capture including the full handshake still decodes handshake packets as binary headers and post-handshake packets as ESC/VP21 data with no regression
