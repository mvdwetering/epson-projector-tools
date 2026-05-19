## 1. Log file infrastructure

- [x] 1.1 Add `_open_session_log(protocol, name_or_slug)` helper to `ui/terminal_app.py` that builds the filename (`<date>T<time>_<protocol>_<slug>.log`), creates the logs directory, opens the file for append, and returns the file handle (or `None` on error with a TUI message)
- [x] 1.2 Add `_slug(text)` utility that sanitises a string for use in a filename (replaces filesystem-unsafe characters with `-`)

## 2. Session log lifecycle

- [x] 2.1 Add `_log_file: Optional[IO]` instance variable to `TerminalApp.__init__`
- [x] 2.2 In `_attach_client()`, close any existing `_log_file`, then call `_open_session_log()` using the protocol and preset name (or `host-port` fallback) from `params`
- [x] 2.3 In `on_unmount()`, close `_log_file` if open

## 3. Log file writing

- [x] 3.1 In `_append_to_log()`, after updating the TUI widget, write the line + newline to `_log_file` and call `flush()` if the file is open

## 4. TUI label

- [x] 4.1 Add a `Label` with id `log-file-label` to the info panel in `compose()`, below the status label
- [x] 4.2 In `_attach_client()`, update `#log-file-label` with the log file basename after opening the file; clear it on failure
