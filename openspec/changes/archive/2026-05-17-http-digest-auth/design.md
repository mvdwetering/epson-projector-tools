## Context

The HTTP transport (`transports/http.py`) currently has no authentication. Real Epson projectors use HTTP Digest authentication (RFC 2617) on their HTTP control interface. Captured traffic from a real device (EH-TW series) shows:

```
WWW-Authenticate: Digest realm="Web Control", nonce="29a493:ab6e88cb8c835a1cd6214a1b83e754a4", qop="auth"
Authorization:    Digest username="EPSONWEB", realm="Web Control", nonce="...", qop=auth, nc=..., cnonce="...", response="..."
```

Key facts established from the real device:
- **Realm**: `"Web Control"` (fixed)
- **Username**: `"EPSONWEB"` (fixed)
- **Algorithm**: MD5 (field absent in `WWW-Authenticate` → RFC 2617 default)
- **qop**: `"auth"`
- No `stale=` support observed; no `algorithm=` field emitted

The real projector nonce format is `<6-hex>:<md5-hash>` (e.g. `"29a493:ab6e88cb8c835a1cd6214a1b83e754a4"`). This appears to be a proprietary structured token. The emulator uses a flat `secrets.token_hex(16)` instead — both are opaque strings per RFC 2617; the client echoes them back unchanged.

## Goals / Non-Goals

**Goals:**
- Protect all HTTP endpoints with Digest auth when `--http-password` is supplied
- Emit a `WWW-Authenticate` header that aiohttp's `DigestAuthMiddleware` can parse and respond to correctly
- Preserve current no-auth behaviour when no password is given

**Non-Goals:**
- Matching the real projector's nonce format exactly
- Replay protection / nonce-count (`nc`) validation
- `stale=true` nonce rotation
- `algorithm=MD5-sess` or SHA-256 support
- Auth on serial or ESC/VP.net transports

## Decisions

### D1: aiohttp `@web.middleware` for auth

Auth is implemented as an `aiohttp.web` middleware function, created via a factory that closes over the pre-computed HA1 hash and the current nonce. This integrates cleanly with `web.Application(middlewares=[...])` and keeps the auth logic contained in `transports/http.py`.

**Alternatives considered:**
- Per-handler checks: more repetitive, easy to miss a new route
- External library (e.g. `aiohttp-digest`): adds a dependency for ~50 lines of well-understood logic

### D2: Pre-compute HA1 at middleware creation

`HA1 = MD5("EPSONWEB:Web Control:<password>")` is computed once when the middleware is constructed, not on every request. Requests only compute `HA2` and `response` per-call.

### D3: Random nonce per challenge, stored in middleware instance

A new `secrets.token_hex(16)` nonce is generated each time a `401` is issued and stored in the middleware. The client must echo this nonce back. On successful auth the nonce is not rotated (the client will reuse it with incrementing `nc`, as the real device allows). On failed auth a new nonce is issued.

**Alternatives considered:**
- Fixed startup nonce: simpler, but a single captured exchange enables permanent replay
- HMAC time-based nonce: stateless verification; adds complexity not needed for an emulator

### D4: `--http-password` CLI argument, no `--http-username`

The username `EPSONWEB` is hardcoded — it matches the real device and is not configurable on real projectors. Adding a username flag would diverge from protocol reality for no benefit.

### D5: No nc validation

The emulator does not track or validate the nonce-count (`nc`) field. The client may send any `nc` value. This is safe for a local emulator; the real device also appears to accept high nc values without complaint.

## Risks / Trade-offs

- **Replay risk** → Acceptable for a local emulator; nonce validation is non-goal
- **MD5 weakness** → MD5 is broken for collision resistance but Digest auth's use of MD5 as a HMAC is still the projector's actual protocol; no alternative
- **Nonce format divergence** → Any client following RFC 2617 will work; only clients that inspect the nonce's internal structure (none known) would notice

## Open Questions

- None. All protocol parameters are confirmed from real device capture.
