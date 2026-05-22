## 1. Configuration Data Wiring

- [x] 1.1 Identify the runtime configuration values needed by the emulator UI (serial port, ESC/VP.net port, HTTP port, auth-required flags) and define a small UI-facing data structure.
- [x] 1.2 Populate that configuration structure in startup flow from the same parsed arguments used to launch transports.
- [x] 1.3 Pass the configuration structure into the Textual app initialization without changing transport behavior.

## 2. TUI Configuration Panel

- [x] 2.1 Add a dedicated configuration panel to the emulator TUI layout that is visible on startup.
- [x] 2.2 Render transport port rows for Serial TCP, ESC/VP.net, and HTTP using the injected runtime configuration values.
- [x] 2.3 Render auth-required status for password-protected transports using clear boolean labels and never display password content.

## 3. Validation And Regression Coverage

- [x] 3.1 Add or update UI-focused tests to verify the configuration panel appears and reflects both default and overridden port values.
- [x] 3.2 Add or update tests for auth-required display states (configured vs not configured) and ensure no password value is rendered.
- [x] 3.3 Run targeted test/smoke checks for emulator startup and TUI behavior to confirm no regressions in existing state/log panels.
