## Context

The main emulator TUI in `ui/app.py` currently formats command log timestamps with `HH:MM:SS`, while the terminal UI already uses `HH:MM:SS.mmm`. This difference makes it harder to compare events across the two interfaces and reduces the usefulness of the emulator log when multiple commands arrive within the same second.

## Goals / Non-Goals

**Goals:**
- Update the emulator TUI command log to show millisecond-precision timestamps.
- Keep the visible log structure unchanged apart from the timestamp precision.
- Match the timestamp semantics already used by the terminal UI so event correlation is straightforward.

**Non-Goals:**
- Changing transport behavior or command processing timing.
- Introducing persistent log files for the emulator TUI.
- Expanding precision beyond milliseconds.

## Decisions

Use the event receipt time already captured in the emulator TUI queue processor and format it as `HH:MM:SS.mmm` at render time. This keeps the change localized to the log display path and avoids touching command handling, transport code, or shared state.

Keep the formatting logic local to the emulator TUI rather than extracting a new shared helper immediately. The terminal already has a private timestamp helper, but introducing a shared utility for a single formatting call would add structure without reducing meaningful complexity. The spec will define the required format so future refactors can consolidate the implementation safely.

## Risks / Trade-offs

- Duplicate timestamp formatting logic between the emulator TUI and terminal UI -> Mitigation: keep the required `HH:MM:SS.mmm` format explicit in the spec and validate behavior at the UI level.
- Slightly wider log lines in the emulator TUI -> Mitigation: only the timestamp segment changes, so the impact is small and predictable.