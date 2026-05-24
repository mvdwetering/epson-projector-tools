## ADDED Requirements

### Requirement: Packet-local protocol dispatch
The dissector SHALL classify each packet independently using only the current packet bytes.

If the payload begins with the 10-byte `ESC/VP.net` magic string, the dissector SHALL decode the packet as ESC/VP.net. If the payload does not begin with that magic string, the dissector SHALL decode the payload as ESC/VP21 data.

#### Scenario: Packet with magic is decoded as ESC/VP.net
- **WHEN** a packet starts with `ESC/VP.net`
- **THEN** the dissector parses and displays ESC/VP.net header and extension-header fields

#### Scenario: Packet without magic is decoded as ESC/VP21
- **WHEN** a packet does not start with `ESC/VP.net`
- **THEN** the dissector displays the packet payload under `ESC/VP21 data`

## REMOVED Requirements

### Requirement: Per-stream phase tracking
**Reason**: Stream-level mode state is not required when ESC/VP.net packets are self-identifying via the magic prefix.
**Migration**: Use packet-local dispatch: magic-prefixed packets decode as ESC/VP.net; non-magic packets decode as ESC/VP21 data.

### Requirement: Mid-session ESC/VP21 detection
**Reason**: Heuristic inference is no longer needed once non-magic packets are always treated as ESC/VP21 payload.
**Migration**: Remove heuristic promotion logic and classify each packet directly by magic presence.

## MODIFIED Requirements

### Requirement: Magic prefix validation
The dissector SHALL verify that packets decoded as ESC/VP.net begin with the 10-byte ASCII string `ESC/VP.net` before decoding further fields.

If the magic is absent, the dissector SHALL decode the payload as ESC/VP21 data instead of passing bytes to the default data dissector.

#### Scenario: Valid magic accepted
- **WHEN** the first 10 bytes of a packet equal `45 53 43 2F 56 50 2E 6E 65 74` (`ESC/VP.net`)
- **THEN** the dissector decodes the remaining ESC/VP.net fields

#### Scenario: Invalid magic falls back to ESC/VP21
- **WHEN** the first 10 bytes do not match `ESC/VP.net`
- **THEN** the packet is shown as `ESC/VP21 data`
