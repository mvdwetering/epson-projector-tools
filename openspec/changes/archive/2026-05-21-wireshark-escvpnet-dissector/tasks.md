## 1. Project scaffold

- [x] 1.1 Create `dissectors/` directory at the repo root
- [x] 1.2 Create `dissectors/escvpnet.lua` with file header comment (protocol name, port, spec reference, Wireshark Lua API version targeted)

## 2. Protocol and field registration

- [x] 2.1 Register the `escvpnet` Proto object with Wireshark (`Proto("escvpnet", "ESC/VP.net Protocol")`)
- [x] 2.2 Define ProtoField entries for all 16-byte header fields: `magic` (bytes), `version` (uint8), `msg_type` (uint8 with value_string table), `reserved` (uint16), `status` (uint8 with value_string table), `num_headers` (uint8)
- [x] 2.3 Define ProtoField entry for `password_data` (bytes)
- [x] 2.4 Define ProtoField entry for `escvp21_data` (string, used for post-handshake payload)
- [x] 2.5 Build `value_string` tables for message types (0x01–0x06) and status codes (0x20 OK, 0x41 Error)

## 3. Header parsing function

- [x] 3.1 Implement `parse_header(tvb, pinfo, tree)` that validates magic prefix and returns `nil` on mismatch
- [x] 3.2 Add magic field to subtree; add `PI_MALFORMED` expert info if packet is shorter than 16 bytes
- [x] 3.3 Add Version field; emit `PI_WARN` expert info if version ≠ `0x10`
- [x] 3.4 Add Type field using value_string (symbolic + numeric display)
- [x] 3.5 Add Reserved field; emit `PI_NOTE` expert info if reserved ≠ `0x0000`
- [x] 3.6 Add Status field using value_string
- [x] 3.7 Add Num Headers field
- [x] 3.8 Return parsed `msg_type` and `status` values to caller

## 4. Post-header payload handling

- [x] 4.1 If `msg_type` is PASSWORD request (0x05) or PASSWORD response (0x06) and bytes remain after offset 16, add them under `password_data` field
- [x] 4.2 For all other handshake messages, note any unexpected trailing bytes with a `PI_NOTE` expert info item

## 5. Per-stream phase tracking

- [x] 5.1 Create a conversation-keyed state table (Lua table indexed by `tostring(pinfo.conversation)`)
- [x] 5.2 In the main dissector function, look up current stream phase (`"handshake"` or `"data"`)
- [x] 5.3 After successfully parsing a CONNECT response (type=0x04) with status `0x20`, set the stream phase to `"data"` for that conversation
- [x] 5.4 When stream phase is `"data"`, skip header parsing and add payload bytes under `escvp21_data` field with label `ESC/VP21 data`

## 6. Wireshark registration

- [x] 6.1 Register the dissector on TCP port 3629 via `DissectorTable.get("tcp.port"):add(3629, escvpnet_proto)`
- [x] 6.2 Verify "Decode As" availability by confirming registration via `tcp.port` table (this is automatic when using the above registration)

## 7. Manual testing

- [x] 7.1 Run the epson emulator and capture a session on port 3629 with `tcpdump -w escvpnet_test.pcap`
- [x] 7.2 Open the pcap in Wireshark with `escvpnet.lua` loaded; verify all handshake fields are labelled correctly
- [x] 7.3 Verify post-handshake ESC/VP21 commands appear under the `escvp21_data` field
- [x] 7.4 Verify expert info items appear for a crafted packet with wrong version byte
- [x] 7.5 Verify expert info items appear for a crafted packet with non-zero reserved bytes
