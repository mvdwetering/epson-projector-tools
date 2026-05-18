## Context

The HTTP transport implements Digest authentication controlled by a `--http-password` CLI argument. That argument passes a plaintext password directly on the command line, making it visible in shell history and `ps aux`. The emulator is a development tool, so a well-known default password is acceptable — what matters is that auth can be enabled without leaking the password through process metadata. Additionally, operators may want to rotate the password during a live session without restarting.

Current data flow:
```
argparse --http-password <str>  →  HttpTransport(password=str)
                                    └─ _make_digest_middleware(password)
                                         └─ ha1 = MD5("EPSONWEB:Web Control:<password>") ← captured once at startup
```

## Goals / Non-Goals

**Goals:**
- Remove the plaintext password from the CLI argument value.
- Provide a hardcoded default password `"httppassword"` used whenever authentication is enabled.
- Allow the password to be changed at runtime via a TUI keypress, taking effect immediately for subsequent requests.
- Preserve all existing Digest auth protocol behavior (realm, algorithm, nonce rotation, etc.).

**Non-Goals:**
- Persistent password storage (file, keychain, environment variable).
- Per-user passwords or multiple credentials.
- Securing the password in memory (this is a dev emulator).

## Decisions

### Decision 1: `--http-password` becomes a boolean flag

**Chosen**: `action="store_true"` in argparse. When present, auth is enabled with the default password. No value is accepted.

**Alternative considered**: Keep it as an optional string with a fallback default (`default="httppassword"`). Rejected because even when a user doesn't set it, the default would appear in `--help` output and might invite passing custom passwords on the CLI in future.

**Rationale**: A boolean flag makes the intent unambiguous — it enables auth, full stop. The password itself is never on the command line.

---

### Decision 2: Mutable password held in a shared `PasswordStore` object

**Chosen**: A minimal `PasswordStore` dataclass (or plain object) with a single `.password: str` attribute, created in `main.py` and passed to both `HttpTransport` and `EmulatorApp`.

```python
class PasswordStore:
    def __init__(self, password: str) -> None:
        self.password = password
```

`HttpTransport` holds a reference. The digest middleware recomputes `ha1` on every request using `store.password`, so a TUI update to `store.password` takes effect immediately — no restart, no re-binding.

**Alternative considered**: Pass a `Callable[[], str]` getter to the transport. Functionally equivalent but more indirection with no benefit.

**Alternative considered**: Use `asyncio.Queue` or observer callback to notify the transport. Overkill — reading `store.password` directly per request is cheaper and simpler.

---

### Decision 3: TUI password change via `Input` widget overlay

**Chosen**: When the operator presses `w`, the TUI pushes a `ModalScreen` (Textual built-in) containing a single `Input` widget pre-filled with the current password. On submit (Enter), `store.password` is updated and the modal is dismissed. On cancel (Escape), nothing changes.

**Alternative considered**: Inline prompt in the footer bar. Textual doesn't provide a native footer input; would require a custom widget.

**Alternative considered**: `Input` widget always visible in a side panel. Unnecessary screen real-estate for an infrequently used feature.

**Rationale**: `ModalScreen` is the idiomatic Textual pattern for ephemeral dialogs. It keeps the existing layout unchanged.

---

### Decision 4: `ha1` recomputed per-request (not cached)

Since the password is mutable, `ha1 = MD5("EPSONWEB:Web Control:<password>")` must be recomputed on each request rather than cached at middleware creation time.

**Performance note**: MD5 on a short string is negligible — this is a dev emulator handling at most a few requests per second.

## Risks / Trade-offs

- **Hardcoded default is publicly known** → For a dev-only emulator this is intentional and documented. Users requiring real security should note this.
- **`ModalScreen` availability** → Textual's `ModalScreen` is available from Textual ≥ 0.27. The project already depends on Textual; version should be verified during implementation.
- **No nonce invalidation on password change** → If a client has a cached `ha1` for the old password and the password changes, the client's next request will get a 401 and will re-authenticate. This is the correct behavior with no extra work needed.
