## Why

Mapped HTTP IR keys currently log the translated internal command (for example, `SOURCE A0`) instead of the received command (`KEY 40`). This hides transport input fidelity in the emulator log and makes troubleshooting command-path behavior harder. Also, key dispatch behavior is currently implemented in HTTP transport code, so behavior differs by connection type.

## What Changes

- Preserve the original received command string in command logs for HTTP `directsend` key dispatch.
- Make key dispatch behavior transport-independent so `KEY <code>` effects are consistent across HTTP, serial TCP, and ESC/VP.net connections.
- Keep existing source-selection key behavior unchanged (no additional source mappings).
- Add IR key mappings for volume control (`VOL INC`, `VOL DEC`) with the same received-command logging fidelity.
- Ensure command observer payloads for mapped key flows report the received command while reflecting success/failure from the executed internal action.
- Add/adjust tests to verify both logging fidelity and unchanged state effects.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `http-transport`: Refine `directsend` key handling requirements so command logs always capture the received command (`KEY <ir_code>`) while delegating KEY behavior to shared engine semantics.
- `escvp21-engine`: Extend KEY command semantics to include shared key dispatch effects across transports, and add `VOL INC`/`VOL DEC` key mappings.

## Impact

- Affected code: shared command semantics in `projector/engine.py` and HTTP transport logging/forwarding in `transports/http.py`.
- Affected behavior: `KEY <code>` behavior is consistent across all transports; emulator TUI/observers continue receiving the original transport command text.
- Testing impact: engine-level and transport-level tests need updates for shared key behavior and logging expectations.
