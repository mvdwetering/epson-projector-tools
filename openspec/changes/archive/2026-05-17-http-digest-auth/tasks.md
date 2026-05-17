## 1. CLI

- [x] 1.1 Add `--http-password` argument to `main.py` argument parser (optional `str`, default `None`)
- [x] 1.2 Pass `password=args.http_password` to `HttpTransport` constructor in `main.py`

## 2. HttpTransport wiring

- [x] 2.1 Add `password: str | None = None` parameter to `HttpTransport.__init__`
- [x] 2.2 When `password` is not `None`, create the Digest auth middleware and pass it to `web.Application(middlewares=[...])`
- [x] 2.3 When `password` is `None`, construct `web.Application()` with no middlewares (existing behaviour)

## 3. Digest auth middleware

- [x] 3.1 Add `_make_digest_middleware(password: str)` factory function in `transports/http.py`
- [x] 3.2 Pre-compute `HA1 = MD5("EPSONWEB:Web Control:<password>")` inside the factory (once at creation)
- [x] 3.3 Store current nonce in the middleware closure (initialise to `secrets.token_hex(16)`)
- [x] 3.4 On request: if `Authorization` header is absent or not `Digest`, issue `401` with `WWW-Authenticate: Digest realm="Web Control", nonce="<current>", qop="auth"` and generate a new random nonce for next challenge
- [x] 3.5 On request with `Digest` header: parse `username`, `nonce`, `nc`, `cnonce`, `qop`, `response` fields
- [x] 3.6 Compute `HA2 = MD5(f"{request.method}:{request.path_qs}")` and `expected = MD5(f"{HA1}:{nonce}:{nc}:{cnonce}:auth:{HA2}")`
- [x] 3.7 If `expected != response`, return `401`; otherwise call `await handler(request)`
- [x] 3.8 Add a comment noting the real projector uses a structured nonce format `<6-hex>:<md5-hash>` (e.g. `"29a493:ab6e88cb8c835a1cd6214a1b83e754a4"`); emulator uses flat `secrets.token_hex(16)` instead — both are opaque per RFC 2617

## 4. Verification

- [x] 4.1 Start emulator without `--http-password`; confirm existing HTTP endpoints work without auth
- [x] 4.2 Start emulator with `--http-password secret`; confirm bare `curl` returns `401` with correct `WWW-Authenticate` header
- [x] 4.3 Confirm an aiohttp client using `DigestAuthMiddleware(login="EPSONWEB", password="secret")` can query `/cgi-bin/json_query` successfully
