## Why

The emulator's main TUI command log currently records timestamps with second-level precision, which makes it harder to correlate closely spaced events and compare emulator activity with the terminal, which already logs at millisecond precision. Bringing the emulator log to the same precision improves diagnostics without changing command behavior.

## What Changes

- Update the emulator TUI command log to display millisecond-precision timestamps instead of second-only timestamps.
- Align the emulator log timestamp format with the terminal log format so operators can compare events across both interfaces more easily.
- Preserve the existing command log structure, transport labeling, and success or error indicators.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `tui`: Refine the command log requirement so emulator log entries include millisecond-precision timestamps.

## Impact

Affected areas include the main emulator TUI in `ui/app.py` and the `tui` OpenSpec capability in `openspec/specs/tui/spec.md`. No protocol behavior, transport behavior, or external dependencies are expected to change.