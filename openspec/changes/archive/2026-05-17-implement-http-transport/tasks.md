## 1. Model Fixes

- [x] 1.1 Rename `VOLUME` → `VOL` in `models/eh_tw3200.yaml`
- [x] 1.2 Verify `KEY` command is present in `models/eh_tw3200.yaml` with `notify_only: true` and `writable: true`

## 2. HTTP Transport — Core Routing

- [x] 2.1 Replace the catch-all route in `transports/http.py` with explicit routes for `/cgi-bin/json_query` and `/cgi-bin/directsend`
- [x] 2.2 Return HTTP 404 for all other paths

## 3. HTTP Transport — json_query Endpoint

- [x] 3.1 Extract `jsoncallback` query parameter; return HTTP 400 if missing
- [x] 3.2 Call `handle_command(state, model, jsoncallback_value)` to process the GET command
- [x] 3.3 Parse the `CMD=value\r:` response and extract the value
- [x] 3.4 Return `{"projector": {"feature": {"reply": "<value>"}}}` as JSON with HTTP 200
- [x] 3.5 Raise `web.HTTPBadRequest` if the engine returns `ERR\r:`

## 4. HTTP Transport — directsend SET Endpoint

- [x] 4.1 Extract the first query parameter as `(CMD, VALUE)` pair
- [x] 4.2 If the command is not `KEY`, call `handle_command(state, model, "CMD VALUE")`
- [x] 4.3 Return HTTP 200 on `\r:` response
- [x] 4.4 Raise `web.HTTPBadRequest` if the engine returns `ERR\r:`

## 5. HTTP Transport — directsend KEY Handler

- [x] 5.1 Implement IR code table mapping TW3200 codes to VP21 actions (per design.md table)
- [x] 5.2 Implement power toggle: read `state.get("PWR")`; call `PWR ON` or `PWR OFF` via engine
- [x] 5.3 Implement mute toggle: read `state.get("MUTE")`; call `MUTE ON` or `MUTE OFF` via engine
- [x] 5.4 Implement source-select keys: call `SOURCE <value>` via engine for `40`, `4D`, `44`, `46`
- [x] 5.5 Implement power-off key (`6C`): call `PWR OFF` via engine
- [x] 5.6 For unmapped IR codes, pass `KEY <code>` to the engine (notify_only fallback)
- [x] 5.7 Raise `web.HTTPBadRequest` for codes that the engine also rejects (`ERR\r:`)

## 6. Verification

- [x] 6.1 Manually test `json_query` with `curl` against the running emulator
- [x] 6.2 Manually test `directsend` SET with `curl` (e.g. `CMODE=15`)
- [x] 6.3 Manually test `directsend` KEY with `curl` (power toggle `3B`, HDMI1 `4D`, mute `3E`)
- [x] 6.4 Confirm unknown path returns HTTP 404
- [x] 6.5 Confirm bad command returns HTTP 400 (not silent 200)
