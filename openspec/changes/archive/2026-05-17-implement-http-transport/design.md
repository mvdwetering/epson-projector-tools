## Context

The HTTP transport currently returns `"HTTP transport not yet implemented"` for all requests. The Home Assistant Epson integration communicates exclusively via the HTTP/CGI protocol, so the emulator cannot be used to test HA automations until this is implemented.

The protocol was reverse-engineered from `epson_projector/projector_http.py`. A full protocol reference is at `openspec/specs/http-transport/protocol-reference.md`.

Current state: `transports/http.py` has a working aiohttp server skeleton, a single catch-all route, and no logic. `projector/engine.py` is pure and handles all ESC/VP21 GET/SET logic. The `KEY` command is already in the model as `notify_only`.

## Goals / Non-Goals

**Goals:**
- `GET /cgi-bin/json_query?jsoncallback=CMD?` → ESC/VP21 GET → JSON response
- `GET /cgi-bin/directsend?CMD=VALUE` → ESC/VP21 SET command
- `GET /cgi-bin/directsend?KEY=<ir_code>` → translate IR code to state change or notify-only
- Rename `VOLUME` → `VOL` in model YAML (correct ESC/VP21 command name)
- Raise an exception on unrecognised or failed commands (not silently swallowed)

**Non-Goals:**
- Authentication or session management
- directsend response body content (HTTP 200 = success; body is ignored by client)
- IR codes beyond the TW3200 supported set
- `/cgi-bin/webconf` page
- Any transport other than HTTP

## Decisions

### 1. Toggle logic lives in the HTTP transport, not the engine

The engine (`handle_command`) is a pure command processor — it has no concept of "toggle". Power and mute toggles require reading current state and issuing a SET. This logic belongs in the HTTP transport's KEY handler, not in the engine.

*Alternatives considered*: Adding a `toggle` operation to the engine. Rejected: it would make the engine stateful and break the clean ESC/VP21 command model.

### 2. IR codes, not ESC/VP21 key codes

The HTTP `directsend?KEY=<code>` parameter uses **IR remote codes** (`ir_codes.py`), not the ESC/VP21 KEY command codes (`key_codes.py`). These are distinct code spaces. `key_codes.py` is irrelevant to the HTTP transport.

Evidence: the HA library uses `KEY=3B` (IR: Power toggle), `KEY=4D` (IR: HDMI1), `KEY=56` (IR: Volume+) — all values that only appear in `ir_codes.py`.

### 3. IR KEY → VP21 state mapping (TW3200)

For IR codes with direct VP21 equivalents, translate and call `handle_command`. For navigation/menu keys, fall through to `handle_command(state, model, "KEY <code>")` which is `notify_only` in the model.

| IR code | Action |
|---------|--------|
| `3B` | Toggle `PWR`: read state, call `PWR ON` or `PWR OFF` |
| `6C` | `PWR OFF` |
| `3E` | Toggle `MUTE`: read state, call `MUTE ON` or `MUTE OFF` |
| `40` | `SOURCE A0` (HDMI2) |
| `4D` | `SOURCE 30` (HDMI1) |
| `44` | `SOURCE 10` (PC) |
| `46` | `SOURCE 40` (Video) |
| `43`, `45` | Unknown source code — raise exception |
| all others | Pass to engine as `KEY <code>` (notify_only) |

### 4. json_query response extraction

`handle_command` returns `"CMD=value\r:"`. Parse by splitting on `=` and stripping `\r:`. Wrap in `{"projector": {"feature": {"reply": "<value>"}}}`.

If `handle_command` returns `ERR\r:`, raise `web.HTTPBadRequest`.

### 5. VOL not VOLUME

The correct ESC/VP21 command name is `VOL`. The model YAML has `VOLUME` as a typo. Rename the key in `models/eh_tw3200.yaml`.

## Risks / Trade-offs

- **Toggle race condition** → Two rapid `KEY=3B` requests could both read the same state and cancel each other out. Mitigation: acceptable for an emulator; the real projector has the same issue. No locking added.
- **Unknown IR codes** → Codes not in the table will reach the engine as `KEY <code>` (notify_only). This is safe — the engine acknowledges without storing.
- **Source code gaps** → Component (`43`) and S-Video (`45`) source codes for the TW3200 are unknown. Raising an exception will surface this if the HA integration ever sends them.

## Open Questions

- What is the correct `SOURCE` value for Component and S-Video on the TW3200?
- Does the real TW3200 respond with a body on directsend? (Needs live capture.)
