## Context

The terminal TUI's left-column connection info panel currently uses six separate label rows: "Connection" (heading), preset name, protocol, host, port, and status. This is verbose and leaves little vertical space for the quick-commands panel below it. Additionally, when the user presses `c` to reconnect while already connected, the `PresetListScreen` opens without any preset pre-selected, so the user must scroll to find their current preset before editing or reconnecting.

## Goals / Non-Goals

**Goals:**
- Merge the connection status into the "Connection" heading label so the panel displays e.g. `Connection  [Connected]` with colour coding inline.
- Merge the port value into the host label so the panel displays e.g. `Host: 192.168.1.50:3629`, removing the standalone port row.
- Track the active preset name on `TerminalApp` so it can be passed to `PresetListScreen` when the connect dialog is reopened.
- `PresetListScreen` accepts an optional `initial_preset_name` argument and auto-selects the matching list item after mount.

**Non-Goals:**
- Redesigning the quick-commands layout or adding new commands (separate change).
- Changing any transport, engine, client, or model code.
- Persisting UI state across restarts.

## Decisions

**D1 — Inline status in Connection header label**

The `#connection-header-label` replaces both the old static `"Connection"` label and the old `#status-label`. It is the single widget updated by `_apply_state()` and `_tick_reconnect_countdown()`. The label uses Rich markup to show the status text coloured (green/red/yellow) after the heading word.

Alternative considered: keep two labels side by side with `Horizontal`. Rejected — introduces extra CSS complexity and may not align cleanly at narrow widths.

**D2 — Merge port into host label**

`_attach_client()` writes a single `"Host:  host:port"` string into `#host-label`, and the `#port-label` widget is removed from `compose()`. This is the simplest change with no CSS impact.

**D3 — Pre-select active preset via constructor argument**

`PresetListScreen` gains an optional `initial_preset_name: str | None` parameter. On mount, after the list is populated, the widget searches for the item whose `_preset["name"]` matches and calls `lv.index = <idx>` to highlight it. `TerminalApp` stores `self._active_preset_name` (updated each time `_attach_client()` is called with a named preset) and passes it to `PresetListScreen` when reopening the connect dialog.

Alternative considered: scan the list by index in `_push_connect_screen`. Same outcome, but requires iterating ListView children outside `PresetListScreen`, leaking internal details. Rejected.

## Risks / Trade-offs

- [Risk] The `#status-label` ID is referenced in CSS rules and in `_apply_state()` / `_tick_reconnect_countdown()`. All references must be updated to `#connection-header-label`. → Mitigation: small, grep-verifiable change scope.
- [Risk] `#port-label` CSS rule is currently absent (port uses no special colour), but compose/attach code references it. → Mitigation: simply remove both the widget and any `query_one("#port-label")` calls; no CSS change needed.
- [Risk] If `initial_preset_name` matches no entry (e.g. preset was deleted), the list opens without a selection. → Acceptable degradation — no error, user just sees the full list.

## Open Questions

None.
