## 1. PasswordStore Shared Object

- [x] 1.1 Add a `PasswordStore` class to `transports/http.py` (or a shared module) with a single `password: str` attribute
- [x] 1.2 Update `HttpTransport.__init__` to accept a `PasswordStore | None` instead of `password: str | None`

## 2. Digest Middleware — Per-Request HA1

- [x] 2.1 Update `_make_digest_middleware` to accept a `PasswordStore` and recompute `ha1` on each request using `store.password` (remove the cached `ha1`)
- [x] 2.2 Verify existing Digest auth scenarios still pass (realm, nonce rotation, qop=auth, correct/incorrect credentials)

## 3. CLI — Boolean `--http-password` Flag

- [x] 3.1 Change `--http-password` in `main.py` from `default=None` string arg to `action="store_true"`
- [x] 3.2 In `main.py`, create a `PasswordStore("httppassword")` when `--http-password` is set and pass it to `HttpTransport`; pass `None` otherwise
- [x] 3.3 Pass the same `PasswordStore` instance to `EmulatorApp` so the TUI can mutate it

## 4. TUI — Runtime Password Change

- [x] 4.1 Add a `ChangePasswordScreen(ModalScreen)` to `ui/app.py` with a single `Input` widget pre-filled with the current password
- [x] 4.2 On submit (Enter), update `store.password` and dismiss the modal
- [x] 4.3 On cancel (Escape), dismiss the modal without changes
- [x] 4.4 Add `Binding("w", "change_password", "Change Password")` to `EmulatorApp.BINDINGS` only when auth is enabled
- [x] 4.5 Implement `action_change_password` to push `ChangePasswordScreen`; guard with a no-op if `store` is `None`
