## ADDED Requirements

### Requirement: Mid-session ESC/VP21 detection
When a packet arrives in handshake phase but the dissector has not observed a CONNECT response (e.g. because Wireshark was started after the handshake completed), the dissector SHALL apply a heuristic to determine whether the payload is ESC/VP21 data.

The heuristic SHALL match payloads that:
- Begin with an uppercase ASCII letter (`A`–`Z`)
- Contain only printable ASCII characters and spaces
- Are terminated by a carriage-return byte (`\r`, `0x0D`)
- Match the general forms: `CMD?\r`, `CMD VALUE\r`, or `CMD=VALUE\r`

If the heuristic matches, the dissector SHALL:
1. Promote the stream to data phase immediately (as if a CONNECT response had been seen)
2. Decode the current packet as ESC/VP21 data
3. Append ` [session inferred]` to the info-column entry for the first such packet

If the heuristic does not match, the existing behaviour is retained: the packet is labelled `[Unknown / non-ESC/VP.net data]`.

#### Scenario: Query command detected mid-session
- **WHEN** a packet arrives in handshake phase with payload `PWR?\r`
- **THEN** the stream is promoted to data phase, the packet is shown as `ESC/VP21 data [session inferred]`, and the payload is displayed as ASCII text

#### Scenario: Set command detected mid-session
- **WHEN** a packet arrives in handshake phase with payload `PWR ON\r`
- **THEN** the stream is promoted to data phase, the packet is shown as `ESC/VP21 data [session inferred]`, and the payload is displayed as ASCII text

#### Scenario: Response command detected mid-session
- **WHEN** a packet arrives in handshake phase with payload `PWR=01\r`
- **THEN** the stream is promoted to data phase, the packet is shown as `ESC/VP21 data [session inferred]`, and the payload is displayed as ASCII text

#### Scenario: Subsequent packets after promotion
- **WHEN** additional packets arrive on the same stream after the stream was promoted via heuristic
- **THEN** they are decoded as normal `ESC/VP21 data` without the `[session inferred]` annotation

#### Scenario: Binary data not misidentified
- **WHEN** a packet arrives in handshake phase whose payload does not match the ESC/VP21 pattern (e.g. starts with a non-uppercase byte or has no `\r` terminator)
- **THEN** the packet is labelled `[Unknown / non-ESC/VP.net data]` and the stream phase is not changed
