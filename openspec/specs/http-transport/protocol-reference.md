# Epson HTTP Transport — Protocol Reference

Reverse-engineered from `epson_projector/projector_http.py` (Home Assistant integration library).

---

## Transport overview

The projector exposes an HTTP/CGI interface on port 80 (emulator default: 8080).  
There are two CGI endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/cgi-bin/json_query` | GET | Query projector state (ESC/VP21 GET) |
| `/cgi-bin/directsend` | GET | Send a command (ESC/VP21 SET or KEY) |

The client sends a `Referer: http://<host>/cgi-bin/webconf` header; the server does not need to validate it.

---

## `GET /cgi-bin/json_query`

Executes an ESC/VP21 GET command and returns the result as JSON.

### Request

```
GET /cgi-bin/json_query?jsoncallback=CMD?
```

The `jsoncallback` query parameter value is a literal ESC/VP21 GET command string, e.g. `PWR?`, `SOURCE?`, `VOL?`.

### Response

```json
{"projector": {"feature": {"reply": "<value>"}}}
```

`<value>` is the raw ESC/VP21 response value (e.g. `"01"` for power on, `"30"` for HDMI1).

### Example

```
GET /cgi-bin/json_query?jsoncallback=PWR?
→ {"projector": {"feature": {"reply": "01"}}}
```

### Error / Busy

When the command is not supported or the projector is busy, the client receives either:
- `STATE_UNAVAILABLE` — raised as `ProjectorUnavailableError` by the client
- `BUSY` (code `2`) — the client retries

---

## `GET /cgi-bin/directsend`

Sends an ESC/VP21 SET command or an IR KEY command. No meaningful response body is expected by the client.

### Request: ESC/VP21 SET

```
GET /cgi-bin/directsend?CMD=VALUE
```

The query parameter key is the ESC/VP21 command name; the value is the operand.

```
GET /cgi-bin/directsend?CMODE=15     →  CMODE 15
GET /cgi-bin/directsend?ASPECT=00    →  ASPECT 00
```

### Request: IR KEY command

```
GET /cgi-bin/directsend?KEY=<ir_code>
```

`<ir_code>` is a hex IR code from `ir_codes.py` (see section below).  
**Note**: these are IR remote codes, NOT the ESC/VP21 KEY command codes (`key_codes.py`).

```
GET /cgi-bin/directsend?KEY=3B       →  Power toggle
GET /cgi-bin/directsend?KEY=4D       →  HDMI1
```

### Response

HTTP 200. The response body is ignored by the client; a minimal body or empty body is acceptable.

---

## IR KEY codes (TW3200)

The `KEY=<ir_code>` command simulates pressing a button on the remote control.
The codes used over HTTP are **IR codes**, not ESC/VP21 KEY command codes.

Discrete Power ON (`A1`) is not universally supported; clients should use Power Toggle (`3B`).

### TW3200 supported IR codes and their VP21 state effect

| IR Code | Remote label | VP21 equivalent |
|---------|-------------|-----------------|
| `3B` | Power (toggle) | Toggle `PWR` (`01`↔`00`) |
| `6C` | Power OFF | `PWR OFF` → `PWR=00` |
| `3C` | Menu | navigation — notify only |
| `3D` | ESC | navigation — notify only |
| `49` | Enter | navigation — notify only |
| `58` | Pointer: Up | navigation — notify only |
| `59` | Pointer: Down | navigation — notify only |
| `5A` | Pointer: Left | navigation — notify only |
| `5B` | Pointer: Right | navigation — notify only |
| `43` | Component | `SOURCE=?` (projector-specific) |
| `44` | PC | `SOURCE=10` |
| `45` | S-Video | `SOURCE=?` (projector-specific) |
| `46` | Video | `SOURCE=40` |
| `40` | HDMI2 | `SOURCE=A0` |
| `4D` | HDMI1 | `SOURCE=30` |
| `3E` | A/V Mute | Toggle `MUTE` (`ON`↔`OFF`) |
| `3F` | Color Mode | notify only (opens menu) |
| `4B` | Pattern | notify only |
| `20` | Aspect | notify only (cycles aspect) |
| `61` | Memory (1) | notify only |
| `87` | Sharpness | notify only (opens menu) |
| `89` | RGBCMY | notify only (opens menu) |
| `88` | Default | notify only (resets menu item) |
| `83` | 1Dγ | notify only (opens menu) |

---

## KEY codes vs IR codes

The repository contains two separate code files:

| File | Codes | Used where |
|------|-------|-----------|
| `key_codes.py` | ESC/VP21 KEY command operands (e.g. `01`=Power, `03`=Menu) | ESC/VP21 serial/TCP transport only |
| `ir_codes.py` | Remote control IR codes (e.g. `3B`=Power, `4D`=HDMI1) | HTTP directsend `KEY=` parameter |

**These are two distinct code spaces.** Code `6A` appears in both with conflicting meanings (`WallShot` in key_codes, `Memory` in ir_codes) — this is likely a documentation inconsistency in the source material.

---

## Command naming

The ESC/VP21 volume command is **`VOL`**, not `VOLUME`. The model YAML must use `VOL`.

The HA library maps:
```python
"VOLUME": [("jsoncallback", "VOL?")]   →  /cgi-bin/json_query?jsoncallback=VOL?
"VOL_UP": [("KEY", "56")]              →  /cgi-bin/directsend?KEY=56
"VOL_DOWN": [("KEY", "57")]            →  /cgi-bin/directsend?KEY=57
```

---

## Client-observed request headers

Sent by the HA client; the emulator does not need to validate these:

```
Accept-Encoding: gzip, deflate
Accept: application/json, text/javascript
Referer: http://<host>:<port>/cgi-bin/webconf
```

---

## Scope for emulator implementation

| Feature | Decision |
|---------|----------|
| `json_query` | Map `jsoncallback` param to `handle_command(state, model, "CMD?")`, extract value, return JSON |
| `directsend` (SET) | Map `CMD=VALUE` param to `handle_command(state, model, "CMD VALUE")` |
| `directsend` (KEY) | Map IR code to VP21 state change per table above; notify_only for navigation keys |
| Response body (directsend) | HTTP 200 = success; body is ignored |
| Error handling | Raise exception (not silently swallowed) |
| KEY code scope | TW3200 supported codes only |
