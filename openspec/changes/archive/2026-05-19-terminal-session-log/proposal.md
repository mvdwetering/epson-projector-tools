## Why

When debugging projector behaviour or validating command responses, it's useful to refer back to an exact record of what was sent and what came back — even when you're no longer near the projector. The terminal TUI currently holds the command log only in memory; everything is lost when the app exits.

## What Changes

- Each new connection session automatically creates a log file on disk
- Log files are written to `~/.config/epson_terminal/logs/` (same XDG location as presets)
- A new file is created when the app starts with a connection, and each time the user switches to a different connection; reconnects stay in the same file
- Filenames encode date, time, protocol, and preset name (or host:port fallback): `2026-05-19T14-32-00_vpnet_living-room.log`
- Every line written to the TUI command log widget is also appended to the log file (including connection attempts, errors, and system messages)
- Log entries use millisecond-precision timestamps matching the TUI display format (`HH:MM:SS.mmm`)
- The info panel in the TUI shows the current log filename (basename only)

## Capabilities

### New Capabilities
- `terminal-session-log`: Per-session persistent log files for the terminal TUI — creation, naming, writing, and TUI visibility

### Modified Capabilities
- `terminal-tui`: Info panel gains a log-filename label; `_append_to_log` gains file-write side-effect

## Impact

- `ui/terminal_app.py`: `_attach_client()` opens a new log file; `_append_to_log()` writes to it; `on_unmount()` closes it; info panel gets a new `Label`
- No new dependencies required (`pathlib` + built-in `open` are sufficient)
- Log files accumulate in `~/.config/epson_terminal/logs/`; no automatic rotation or cleanup in scope
