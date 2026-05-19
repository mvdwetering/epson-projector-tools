## Context

The ESC/VP.net transport (`transports/vpnet.py`) performs a binary HELLO/CONNECT handshake before entering the ESC/VP21 pipe. The spec defines an optional Password header (18 bytes: 1-byte id + 1-byte attribute + 16-byte null-padded string) that can be included in the CONNECT packet. The transport currently ignores all extra headers via `_skip_extra_headers()`. The client (`client/vpnet.py`) always sends CONNECT with 0 headers.

The HTTP transport already has a `PasswordStore` object (a mutable holder for a plaintext password string) and the emulator TUI has a `w` keybinding that changes it at runtime. The same pattern can be extended to the ESC/VP.net transport.

## Goals / Non-Goals

**Goals:**
- Enforce an optional password on the ESC/VP.net CONNECT handshake (server side)
- Send the password in the CONNECT header from the client (client side)
- Share one `PasswordStore` between HTTP and ESC/VP.net so a single `w` keypress changes both
- Show the password field in the terminal TUI connection form for `vpnet` (currently HTTP-only)
- Default password `"emulatorpassword"` when either `--http-password` or `--vpnet-password` is enabled

**Non-Goals:**
- The `PASSWORD` packet (type `0x02`) for checking or changing the password via the protocol
- Digest or hashed credential exchange (ESC/VP.net uses plaintext)
- Session-mode keepalives or timeout enforcement
- Persisting the ESC/VP.net password across emulator restarts

## Decisions

### D1: Shared `PasswordStore` for HTTP and ESC/VP.net

**Chosen**: One `PasswordStore` instance, created in `main.py` when `--password` is supplied, passed to both `HttpTransport` and `VpnetTransport`. The store's `.password` attribute is compared directly in the vpnet handshake.

**Alternative considered**: Separate `--http-password` and `--vpnet-password` flags. Rejected because the user wants one password for the entire emulator. Two flags would let them be configured independently, creating silent divergence.

**Alternative considered**: Pass a plain `str | None` to `VpnetTransport`. Rejected because it would make runtime password changes impossible without transport restart, whereas a mutable store allows it.

---

### D2: Single `--password` flag replaces `--http-password` (**BREAKING**)

**Chosen**: `--http-password` is removed and replaced by `--password` (boolean `store_true`). When supplied, `PasswordStore("emulatorpassword")` is created and passed to both transports. When absent, both transports are unauthenticated.

**Rationale**: One flag, one password, one concept. The old `--http-password` name implied HTTP-only scope, which is no longer true.

**Alternative considered**: Keep `--http-password` and add `--vpnet-password`. Rejected by user — they want a single flag.

**Alternative considered**: `--password` accepts an optional value (the password string itself). Rejected to avoid leaking the password through `ps aux` and shell history — the boolean flag pattern already established for HTTP is the right model.

---

### D3: Client always sends password header if password is non-empty (Strategy A)

**Chosen**: `VpnetClient` always includes the Password header in CONNECT when `password != ""`. No probe-then-retry.

**Alternative considered**: Send CONNECT without a password first; retry with password on `0x41`. Rejected because it adds a TCP round-trip and extra state for no practical gain in a dev emulator context.

---

### D4: Parse, not skip, CONNECT extra headers

**Chosen**: Replace `_skip_extra_headers()` call in the CONNECT path with a new `_parse_extra_headers()` helper that returns a `dict[int, tuple[int, bytes]]` mapping header id → (attribute, 16-byte data). HELLO still uses the skip helper (HELLO never carries headers in practice).

**Alternative considered**: Keep skipping and use a separate boolean. Rejected as it would require reading the byte stream twice or buffering.

---

### D5: Reject on mismatch before writing the response; close connection afterward

**Chosen**: On password failure, write the error response (`0x41` or `0x43`) and then close the TCP connection. This matches the spec's "the server cuts off the TCP connection" wording.

**Status codes used:**
- `0x41` Unauthorized — password required but no Password header sent
- `0x43` Forbidden — Password header present but value wrong
- `0x20` OK — correct password, or no password configured

## Risks / Trade-offs

- **`--http-password` removed** → Any scripts using `--http-password` must be updated to `--password`. The password default also changes from `"httppassword"` to `"emulatorpassword"`.
- **Plaintext password on wire** → ESC/VP.net uses cleartext passwords by design (per spec). This is a protocol limitation, not an implementation choice.
- **No password change via `PASSWORD` packet** → A real projector's admin UI can set/clear the password via the `PASSWORD` packet (type `0x02`). The emulator only enforces the password; it does not allow changing it through the protocol. Runtime change is only possible through the TUI `w` keybinding.
