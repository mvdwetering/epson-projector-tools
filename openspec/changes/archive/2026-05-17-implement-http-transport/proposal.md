## Why

The HTTP transport is currently a non-functional stub. The Home Assistant Epson integration uses the HTTP/CGI protocol to control projectors, so without a working HTTP transport the emulator cannot be used to test HA-based automations. The protocol has now been reverse-engineered from the HA library and is fully understood.

## What Changes

- Implement `GET /cgi-bin/json_query` — translates `jsoncallback=CMD?` to an ESC/VP21 GET and returns a JSON response
- Implement `GET /cgi-bin/directsend` — translates `CMD=VALUE` to an ESC/VP21 SET command
- Implement IR KEY handling in directsend — maps `KEY=<ir_code>` to projector state changes for all TW3200-supported IR codes
- Fix model YAML: rename `VOLUME` → `VOL` (correct ESC/VP21 command name)
- Error handling: raise an exception for unrecognised or failed commands (not silently swallowed)

## Capabilities

### New Capabilities

_(none — all capabilities exist; this change fills in real requirements for existing stubs)_

### Modified Capabilities

- `http-transport`: Replace stub requirements with full json_query / directsend / KEY-IR behaviour
- `model-definition`: `VOLUME` command renamed to `VOL`; KEY command IR semantics clarified

## Impact

- `transports/http.py` — primary implementation target
- `models/eh_tw3200.yaml` — rename `VOLUME` → `VOL`
- `openspec/specs/http-transport/spec.md` — requirements updated
- `openspec/specs/model-definition/spec.md` — VOL naming requirement added
- No changes to serial or ESC/VP.net transports
- No changes to the engine (`projector/engine.py`) — KEY toggle logic lives in the transport
