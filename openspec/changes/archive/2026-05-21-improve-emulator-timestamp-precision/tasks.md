## 1. Emulator log timestamp formatting

- [x] 1.1 Update the emulator TUI command log path in `ui/app.py` to format timestamps as `HH:MM:SS.mmm`
- [x] 1.2 Keep the existing transport label and success/error markers unchanged while applying the new timestamp format

## 2. Validation

- [x] 2.1 Verify the `tui` OpenSpec requirement is satisfied by confirming emulator log entries show millisecond precision for closely spaced commands
- [x] 2.2 Run the relevant focused validation for the TUI slice and confirm no regressions in log rendering