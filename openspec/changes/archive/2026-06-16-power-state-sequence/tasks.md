## 1. Model layer — parse power metadata

- [x] 1.1 Add `warmup_seconds: float`, `cooldown_seconds: float`, and `supports_comms_standby: bool` fields to `ModelDef` in `projector/model.py`
- [x] 1.2 Parse `executionTimes` array in `_load_json_model`: extract warmup seconds from the first `"PWR ON"` entry and cooldown seconds from the first `"PWR OFF"` / `"Normal"` entry; fall back to `5.0` and `3.0` respectively
- [x] 1.3 Detect `supports_comms_standby` by scanning `PWR?` query `enumValues` for an entry with `code == "04"` during `_aggregate_commands`
- [x] 1.4 Expose a `standby_state` property on `ModelDef` that returns `"04"` if `supports_comms_standby` else `"00"`

## 2. PowerSequencer — new module

- [x] 2.1 Create `projector/power.py` with a `PowerSequencer` class
- [x] 2.2 Implement `request_on(state, model) -> bool`: sets `PWR` to `"02"`, schedules asyncio task to set `PWR` to `"01"` after `model.warmup_seconds`; returns `False` if already transitioning or already on
- [x] 2.3 Implement `request_off(state, model) -> bool`: sets `PWR` to `"03"`, schedules asyncio task to set `PWR` to `model.standby_state` after `model.cooldown_seconds`; returns `False` if already transitioning or in standby
- [x] 2.4 Implement `cancel()`: cancels the in-flight asyncio task if any; safe to call when idle
- [x] 2.5 Add `is_transitioning` property: `True` when `PWR` is `"02"` or `"03"`

## 3. Engine — delegate PWR to sequencer

- [x] 3.1 Add optional `power_sequencer: PowerSequencer | None = None` parameter to `handle_command` in `projector/engine.py`
- [x] 3.2 In `_handle_set`, intercept `cmd == "PWR"` when a sequencer is provided: call `request_on` / `request_off` based on mapped value; return `\r:` on acceptance, `ERR\r:` on rejection
- [x] 3.3 Preserve existing synchronous behaviour when no sequencer is provided (no-sequencer path unchanged)

## 4. Application wiring — startup and transport injection

- [x] 4.1 In `main.py`, create a `PowerSequencer` instance alongside `ProjectorState`
- [x] 4.2 Pass the sequencer to every `handle_command` call site in `transports/serial.py`, `transports/vpnet.py`, and `transports/http.py`

## 5. TUI — keybinding and model-reload integration

- [x] 5.1 Pass the `PowerSequencer` into the emulator `App` (e.g. as constructor argument) in `ui/app.py`
- [x] 5.2 Update `action_toggle_power` to cycle `PWR` through the sequence `00`/`04` → `02` → `01` → `03` → `00`/`04` by writing directly to state; cancel any in-flight sequencer task first
- [x] 5.3 Call `sequencer.cancel()` at the start of the model-reload sequence in `ui/app.py` before replacing state

## 6. Tests

- [x] 6.1 Add unit tests for `PowerSequencer.request_on` / `request_off` state progression (use short delays and `asyncio.sleep` mocking or real short sleeps)
- [x] 6.2 Add unit tests for `PowerSequencer` rejection scenarios (mid-transition, already-on, already-standby)
- [x] 6.3 Add unit tests for `handle_command` with sequencer: acceptance, rejection, and no-sequencer fallback
- [x] 6.4 Add unit test for model parsing: `warmup_seconds`, `cooldown_seconds`, `supports_comms_standby`, and `standby_state` on LS11000 and TW3200 fixtures
