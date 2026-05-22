## Context

The emulator Textual UI currently emphasizes live projector state and command logs, but not startup/runtime configuration. Operators frequently need to confirm which ports are in use and whether password-protected access is enabled, especially when validating network setup or reproducing integration issues.

Configuration is already known at startup in `main.py` (selected model, transport port values, password argument presence) and passed into transport startup. The design should expose this existing data in the UI without introducing new protocol behavior or mutable runtime configuration state.

## Goals /
 Non-Goals

**Goals:**
- Show active transport ports (serial TCP, ESC/VP.net, HTTP) directly in the emulator UI.
- Show whether password authentication is required for each transport that supports auth.
- Ensure displayed values are derived from actual runtime configuration inputs to avoid UI drift.
- Keep the implementation low risk and localized to startup wiring plus TUI rendering.

**Non-Goals:**
- Changing transport protocols or authentication mechanisms.
- Adding runtime editing of port/auth settings from this panel.
- Introducing persistence or new config file formats.

## Decisions

1. Introduce an immutable UI config snapshot passed into the TUI app
- Decision: Build a small configuration structure at startup (e.g., serial_port, vpnet_port, http_port, http_auth_required, vpnet_auth_required) and pass it to the Textual app constructor.
- Rationale: This avoids recomputing values from multiple places and guarantees the panel reflects the same values used to launch servers.
- Alternative considered: Query transport objects after startup. Rejected because it couples UI to transport internals and complicates lifecycle ordering.

2. Add a dedicated "Configuration" panel in the main emulator UI
- Decision: Render a static panel near existing status/log widgets with explicit rows for each transport.
- Rationale: Operators can quickly inspect configuration without navigating modal views or logs.
- Alternative considered: Inject one-time log entries with config values. Rejected because logs scroll and are less discoverable.

3. Represent auth requirement as explicit yes/no status
- Decision: Display a normalized boolean status (`Required` / `Not required`) per relevant transport.
- Rationale: Makes security posture obvious and avoids exposing secret material.
- Alternative considered: Showing masked password length or placeholder values. Rejected because it adds little value and can be misinterpreted.

4. Keep panel values static for process lifetime
- Decision: Treat configuration panel as startup snapshot; only projector state and command log remain dynamic.
- Rationale: Current ports/auth flags are startup-defined, and static rendering avoids unnecessary observer/event plumbing.
- Alternative considered: Live-updating config through state observers. Rejected as unnecessary complexity for current behavior.

## Risks / Trade-offs

- [Risk] UI clutter on narrow terminals due to additional panel rows. -> Mitigation: Keep labels concise and favor compact row formatting.
- [Risk] Drift between displayed and actual configuration if values are duplicated manually. -> Mitigation: Build the UI snapshot from the same parsed arguments used to start transports.
- [Risk] Ambiguity for transports without auth support. -> Mitigation: Display auth status only where applicable, with clear "N/A" or omitted field conventions.

## Migration Plan

No data or protocol migration is required.

Implementation rollout:
1. Add startup wiring to construct and pass UI configuration snapshot.
2. Add Configuration panel rendering in the Textual app.
3. Add/update tests to validate panel content for different startup arguments.
4. Run existing emulator startup and smoke tests.

Rollback strategy:
- Revert UI snapshot wiring and configuration panel rendering changes; transports and engine behavior remain unaffected.

## Open Questions

- Should ESC/VP.net auth-required status be shown now, or only HTTP auth-required status if VP.net auth is not configured in a given run mode?
- Is the desired auth label wording `Required/Not required` or `Enabled/Disabled` for consistency with other UI labels?
