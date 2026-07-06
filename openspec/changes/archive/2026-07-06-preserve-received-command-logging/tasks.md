## 1. KEY Logging Fidelity

- [ ] 1.1 Ensure command observer logging always emits the received command string (`KEY <ir_code>`) for HTTP KEY requests, including mapped-key paths.
- [ ] 1.2 Preserve existing state effects and error behavior while keeping log fidelity for mapped KEY flows.

## 2. Shared KEY Dispatch Semantics

- [ ] 2.1 Move KEY dispatch behavior into shared engine semantics so KEY effects are consistent across HTTP, serial TCP, and ESC/VP.net.
- [ ] 2.2 Keep existing source-selection key mappings unchanged.
- [ ] 2.3 Add requested volume key mappings for `VOL INC` and `VOL DEC` in shared KEY dispatch behavior.

## 3. Verification

- [ ] 3.1 Add or update HTTP transport tests to assert mapped key requests log the received command (for example `KEY 40`) while applying mapped state changes.
- [ ] 3.2 Add cross-transport regression tests to assert identical KEY outcomes via HTTP, serial TCP, and ESC/VP.net.
- [ ] 3.3 Add or update regression coverage for `VOL INC`/`VOL DEC` KEY mappings in shared behavior.
- [ ] 3.4 Add or update regression coverage for non-mapped KEY handling to confirm notify-only/error behavior remains correct.
- [ ] 3.5 Run relevant test targets and confirm no regressions in engine and transport behavior.
