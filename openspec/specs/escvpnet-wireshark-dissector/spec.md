### Requirement: Dissector registers on ESC/VP.net TCP port
The dissector SHALL register itself with Wireshark on TCP port 3629 and SHALL also be available via "Decode As" for any TCP stream.

#### Scenario: Auto-registration on port 3629
- **WHEN** Wireshark captures or opens a pcap containing TCP traffic on port 3629
- **THEN** the dissector is automatically applied to that stream without user intervention

#### Scenario: Manual decode-as
- **WHEN** the user right-clicks a TCP stream and selects "Decode As" → `escvpnet`
- **THEN** the dissector is applied to that stream

---

### Requirement: Magic prefix validation
The dissector SHALL verify that each handshake packet begins with the 10-byte ASCII string `ESC/VP.net` before decoding further fields. If the magic is absent the dissector SHALL pass the bytes to the default data dissector.

#### Scenario: Valid magic accepted
- **WHEN** the first 10 bytes of a packet equal `45 53 43 2F 56 50 2E 6E 65 74` (`ESC/VP.net`)
- **THEN** the dissector decodes the remaining header fields

#### Scenario: Invalid magic rejected
- **WHEN** the first 10 bytes do not match `ESC/VP.net`
- **THEN** the dissector labels the packet as `[Unknown / non-ESC/VP.net data]` and does not parse further

---

### Requirement: 16-byte header field decoding
The dissector SHALL decode all fields of the 16-byte ESC/VP.net header and display them as named fields in the Wireshark packet detail pane.

Header layout (per specification):
| Offset | Length | Field |
|--------|--------|-------|
| 0 | 10 | Magic (`ESC/VP.net`) |
| 10 | 1 | Version (SHALL be `0x10`) |
| 11 | 1 | Message type |
| 12 | 2 | Reserved |
| 14 | 1 | Status |
| 15 | 1 | Number of headers |

#### Scenario: All fields labelled
- **WHEN** a valid 16-byte handshake packet is dissected
- **THEN** the packet detail pane shows individual rows for: Magic, Version, Type, Reserved, Status, Num Headers

#### Scenario: Packet shorter than 16 bytes
- **WHEN** the captured data for a handshake packet is fewer than 16 bytes
- **THEN** the dissector adds a Wireshark expert info item of severity `PI_MALFORMED` and does not attempt to read beyond the available bytes

---

### Requirement: Message type symbolic names
The dissector SHALL display message type bytes as human-readable names alongside the numeric value.

Defined types (per specification):
| Value | Name |
|-------|------|
| `0x01` | HELLO request |
| `0x02` | HELLO response |
| `0x03` | CONNECT request |
| `0x04` | CONNECT response |
| `0x05` | PASSWORD request |
| `0x06` | PASSWORD response |

#### Scenario: Known type displayed symbolically
- **WHEN** the type byte is `0x01`
- **THEN** the Type field displays `HELLO request (0x01)`

#### Scenario: Unknown type displayed numerically
- **WHEN** the type byte is not in the defined set
- **THEN** the Type field displays `Unknown (0xNN)` where `NN` is the hex value

---

### Requirement: Status code symbolic names
The dissector SHALL display status bytes as human-readable names.

Defined statuses (per specification):
| Value | Name |
|-------|------|
| `0x20` | OK |
| `0x41` | Error |

#### Scenario: OK status displayed
- **WHEN** the status byte is `0x20`
- **THEN** the Status field displays `OK (0x20)`

#### Scenario: Error status displayed
- **WHEN** the status byte is `0x41`
- **THEN** the Status field displays `Error (0x41)`

---

### Requirement: Per-stream phase tracking
The dissector SHALL maintain per-conversation state to detect when the ESC/VP.net handshake is complete and the stream has entered ESC/VP21 data mode.

The handshake is considered complete after a CONNECT response with status `0x20` (OK) has been seen in the server-to-client direction.

#### Scenario: Handshake packets decoded as binary
- **WHEN** packets arrive before the CONNECT response
- **THEN** each packet is decoded using the 16-byte binary header format

#### Scenario: Post-handshake data decoded as ESC/VP21 text
- **WHEN** a packet arrives after a successful CONNECT response has been seen on the stream
- **THEN** the dissector labels the packet as `ESC/VP21 data` and displays the payload bytes as ASCII text

---

### Requirement: PASSWORD message payload labelling
The dissector SHALL label the payload of PASSWORD request and response messages as a distinct field (`password_data`) without interpreting or masking the content.

#### Scenario: PASSWORD request payload shown
- **WHEN** a PASSWORD request packet (type `0x05`) is dissected
- **THEN** any bytes beyond the 16-byte header are shown under a `password_data` field as raw bytes

---

### Requirement: Wireshark expert info on protocol violations
The dissector SHALL emit Wireshark expert info items for detectable protocol violations.

Violations to detect:
- Version byte not equal to `0x10`
- Reserved bytes not equal to `0x0000`
- Packet length less than 16 bytes during handshake phase

#### Scenario: Wrong version flagged
- **WHEN** the version byte is not `0x10`
- **THEN** an expert info item with severity `PI_WARN` and group `PI_PROTOCOL` is added noting the unexpected version value

#### Scenario: Non-zero reserved bytes flagged
- **WHEN** the reserved field is not `0x0000`
- **THEN** an expert info item with severity `PI_NOTE` is added noting the reserved field value

---

### Requirement: Single self-contained Lua file
The dissector SHALL be delivered as a single file `dissectors/escvpnet.lua` with no external Lua library dependencies beyond the Wireshark built-in Lua API.

#### Scenario: Installation by file copy
- **WHEN** `escvpnet.lua` is copied into the Wireshark personal plugins directory and Wireshark is restarted
- **THEN** the dissector is active with no additional configuration

#### Scenario: No Python emulator dependency
- **WHEN** the file is used in an environment where the epson_emulator Python package is not installed
- **THEN** the dissector operates without errors
