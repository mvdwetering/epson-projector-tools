## 1. Update Dissector Classification Logic

- [x] 1.1 Remove per-conversation state tables and related phase-transition logic from `dissectors/escvpnet.lua`
- [x] 1.2 Remove mid-session ESC/VP21 heuristic function and inferred-session annotation handling
- [x] 1.3 Implement packet-local dispatch: decode as ESC/VP.net only when magic prefix is present; otherwise decode as ESC/VP21 data

## 2. Preserve ESC/VP.net Parsing and Validation

- [x] 2.1 Keep fixed-header and extension-header parsing unchanged for magic-prefixed packets
- [x] 2.2 Ensure expert info checks for malformed ESC/VP.net packets still trigger in the magic-prefixed path
- [x] 2.3 Update info-column strings to reflect stateless behavior (no session-inferred labeling)

## 3. Verification

- [x] 3.1 Validate with a capture containing handshake packets that ESC/VP.net fields still decode correctly
- [x] 3.2 Validate with a mid-session capture (no handshake) that packets are displayed as ESC/VP21 data
- [x] 3.3 Validate mixed/reconnect captures to confirm behavior does not depend on prior stream packets
