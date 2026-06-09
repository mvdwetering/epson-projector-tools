## Why

The emulator currently returns `\r:` for null and successful SET acknowledgments, but real Epson projectors return only `:`. Aligning this behavior now avoids protocol mismatches in clients and tests that depend on projector-accurate framing.

## What Changes

- Update ESC/VP21 command handling so a null command (`\r`) returns only `:`.
- Update successful SET acknowledgments to return only `:`.
- Keep query responses and error responses unchanged unless explicitly covered by existing requirements.
- Add or update tests to verify the corrected acknowledgment framing behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `escvp21-engine`: Change requirements for null-command and successful SET acknowledgment framing to return `:` (without leading carriage return).

## Impact

- Affected code: command handling in `projector/engine.py` and any helper paths that format ESC/VP21 acknowledgments.
- Affected tests: engine/transport behavior tests that assert SET or null-command response bytes.
- API/protocol impact: emulator wire responses become projector-accurate for null and SET acknowledgments.
