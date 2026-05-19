## Context

The terminal TUI (`ui/terminal_app.py`) maintains a command log only in memory via a `TextArea` widget. All command/response pairs, system messages, and connection events are routed through `_append_to_log(line: str)` and lost on exit. The presets config already lives at `~/.config/epson_terminal/` (via `platformdirs`).

## Goals / Non-Goals

**Goals:**
- Write every log line to disk in real time as it is appended to the TUI widget
- Create one log file per connection session; reconnects stay in the same file
- Name files to be self-describing and sort chronologically: `<ISO-date>T<time>_<protocol>_<name-or-host-port>.log`
- Show the current log filename in the TUI info panel
- Close the file cleanly on app exit and before opening a new session file

**Non-Goals:**
- Log rotation, size limits, or automatic cleanup
- Configurable log directory
- Structured (JSON/CSV) log format — plain text is sufficient for the use case
- Logging anything before a connection is established (pre-connection screens have no useful command data)

## Decisions

### D1: Hook point — `_attach_client()` opens the log file

`_attach_client()` is called in exactly two cases: app startup (CLI preset) and `_apply_new_connection()` (user picks/creates a connection). It is **not** called on reconnects. This makes it the natural place to close any previous log file and open a new one, with no risk of accidentally splitting a reconnect across two files.

Alternative considered: open on first write (lazy). Rejected — it adds state complexity and the file name wouldn't be known until the first write.

### D2: Write in `_append_to_log()` with immediate flush

Every call to `_append_to_log(line)` already routes all output (commands, responses, system messages). Adding `file.write(line + "\n"); file.flush()` there requires no other changes to the logging pipeline. `flush()` after every line ensures the file is useful even if the app crashes.

Alternative considered: batch writes on a timer. Rejected — adds complexity and risks data loss on crash.

### D3: Log directory follows existing XDG convention

Presets already live in `platformdirs.user_config_dir("epson_terminal")`. Logs go to a `logs/` subdirectory of the same root. Created with `mkdir(parents=True, exist_ok=True)` on first use. No new dependency.

### D4: Filename uses `_` as separator, `:` replaced with `-`

`<YYYY-MM-DD>T<HH-MM-SS>_<protocol>_<slug>.log`

- ISO 8601 date prefix → alphabetical == chronological sort
- Protocol included to disambiguate sessions to the same host on different transports
- Preset name used when available; `<host>-<port>` fallback for unsaved connections
- Slug sanitised: spaces and characters unsafe on common filesystems replaced with `-`

### D5: TUI label shows basename only

The full path is predictable (`~/.config/epson_terminal/logs/`). Showing only the filename in the info panel keeps the panel compact. Label is cleared when no log is open.

## Risks / Trade-offs

- **Disk space accumulation** → No mitigation in scope; files are small (text, one per session). Users can delete old files manually.
- **Filename collision** (two sessions started in the same second with the same preset) → Last one wins on open (both append to same file). Extremely unlikely in practice; not worth adding sub-second precision to the filename.
- **Non-ASCII preset names** → Sanitisation replaces them with `-`; the file is still created and works correctly.
- **Read-only filesystem** → File open fails silently; TUI continues working without persistence. An error is logged to the TUI widget instead.
