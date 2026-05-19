## 1. Emulator Transport (server side)

- [x] 1.1 Add `_parse_extra_headers(reader, count) -> dict[int, tuple[int, bytes]]` helper to `transports/vpnet.py` that reads `count * 18` bytes and returns a dict of `{header_id: (attribute, 16-byte data)}`
- [x] 1.2 Update `VpnetTransport.__init__` to accept `password_store: PasswordStore | None = None`
- [x] 1.3 Update `_handshake()` in `VpnetTransport`: after reading the CONNECT packet, call `_parse_extra_headers()` instead of `_skip_extra_headers()`; extract the Password header (id `0x01`) if present
- [x] 1.4 Implement password enforcement logic in `_handshake()`: if `password_store` is set and no Password header → respond with `0x41` and return `False`; if Password header present but wrong → respond with `0x43` and return `False`; otherwise → respond with `0x20` and return `True`

## 2. Client (VpnetClient)

- [x] 2.1 Add `password: str = ""` parameter to `VpnetClient.__init__`
- [x] 2.2 Add `_make_connect_packet() -> bytes` helper that returns a 16-byte CONNECT packet (0 headers) when `self._password` is empty, or a 34-byte packet (1 Password header, null-padded to 16 bytes) when non-empty
- [x] 2.3 Update `_handshake()` in `VpnetClient` to call `_make_connect_packet()` instead of `_make_packet(_TYPE_CONNECT)`
- [x] 2.4 Update `_handshake()` to handle CONNECT response `0x41` (raise `ConnectionError("Projector requires a password")`) and `0x43` (raise `ConnectionError("Wrong ESC/VP.net password")`)

## 3. CLI and PasswordStore wiring

- [x] 3.1 Replace `--http-password` with a single `--password` boolean argument in `main.py`
- [x] 3.2 Update `main.py` to create `PasswordStore("emulatorpassword")` when `--password` is given and pass the shared instance to both `HttpTransport` and `VpnetTransport`

## 4. Terminal client wiring

- [x] 4.1 Update `_build_client()` in `terminal.py` to pass `password` to `VpnetClient(host, port, password=password)`

## 5. Terminal TUI

- [x] 5.1 Update `_update_password_visibility()` in `ui/terminal_app.py` to show the password field for both `vpnet` and `http` (currently `http` only)
- [x] 5.2 Update the password field label from `"Password (HTTP only):"` to `"Password (ESC/VP.net / HTTP):"`
