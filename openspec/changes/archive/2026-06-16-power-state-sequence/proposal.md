## Why

The emulator instantly flips the `PWR` value between standby and lamp-on, skipping the intermediate warmup and cooldown states that real Epson projectors go through. This makes the emulator unsuitable for testing clients that poll `PWR?` and act on transitional states (02 warmup, 03 cooldown).

## What Changes

- The emulator's `PWR` value will transition through the correct state sequence with configurable delays rather than jumping directly to the target state.
- Power-on sequence: `00`/`04` → (receive `PWR ON`) → `02` (warmup) → `01` (normal) after warmup delay.
- Power-off sequence: `01` → (receive `PWR OFF`) → `03` (cooldown) → `00` (standby, or `04` if the model supports communication standby) after cooldown delay.
- `PWR ON` and `PWR OFF` commands are rejected with `ERR` if the projector is already mid-transition (in state `02` or `03`).
- The `p` keybinding in the emulator TUI will respect the current state and trigger the appropriate next transition rather than blindly toggling.
- Warmup and cooldown durations are sourced from the model's `executionTimes` data where available; a sensible default is used otherwise.

## Capabilities

### New Capabilities

- `power-state-sequence`: Timed, sequential power state transitions (standby → warmup → normal → cooldown → standby) driven by asyncio tasks, with per-model configurable durations and correct handling of mid-transition command rejection.

### Modified Capabilities

- `escvp21-engine`: `PWR ON`/`PWR OFF` handling changes — commands are rejected during transitions and the engine must schedule async state progression instead of immediately writing the target value.
- `tui`: The `p` keybinding behaviour changes to trigger the correct transition based on the current state; the TUI must cancel in-flight transition tasks when a model switch occurs.

## Impact

- `projector/engine.py` — `handle_command` needs to detect `PWR ON`/`PWR OFF`, check current state, and either reject (mid-transition) or hand off to a new power-sequencing subsystem.
- `projector/state.py` — May need a lightweight async task handle stored on state so the TUI and transports can cancel an in-flight transition on model reload.
- `projector/model.py` — Parse warmup and cooldown durations from `executionTimes`; expose on `ModelDef`; determine whether model supports state `04`.
- `ui/app.py` — Update `action_toggle_power` to respect current `PWR` state.
