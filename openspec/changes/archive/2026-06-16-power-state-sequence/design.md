## Context

The emulator currently handles `PWR ON` and `PWR OFF` commands through the generic `_handle_set` path in `projector/engine.py`. The `set_map` for the `PWR` command maps `ON → "01"` and `OFF → "00"`, so the state is updated immediately and synchronously. There are no intermediate states, no timing, and no rejection of in-flight commands.

Real Epson projectors expose five `PWR?` response codes: `00` (standby, network off), `01` (lamp on / normal), `02` (warmup), `03` (cooldown), and `04` (communication standby, network on). The intermediate states `02` and `03` represent hardware phases that take real time (e.g. 30 s warmup for LS11000), and during those phases further `PWR ON`/`PWR OFF` commands are rejected with `ERR`.

The `p` key in the TUI today calls `action_toggle_power`, which reads the current `PWR` value and sends either `PWR ON` or `PWR OFF` through `handle_command`. The intent going forward is to keep the key useful as a cycle-through-states shortcut even though the hardware only accepts `PWR ON` / `PWR OFF` at the right times.

## Goals / Non-Goals

**Goals:**

- Emit the correct `PWR?` status value at every point in the power cycle.
- Advance through the sequence automatically with configurable delays (warmup, cooldown).
- Reject `PWR ON` / `PWR OFF` commands with `ERR` when a transition is already in progress.
- Start the emulator in standby (`00` or `04`) rather than lamp-on.
- Determine the correct standby state (`00` vs `04`) from model enum values.
- Parse warmup / cooldown durations from the model's `executionTimes` JSON array.
- Cancel in-flight transitions cleanly on model reload.
- Make the `p` keybinding follow the correct cycle.

**Non-Goals:**

- Emulating actual warmup/cooldown delays at realistic wall-clock lengths by default (delays are configurable and default to short values for developer convenience).
- Exposing `02` / `03` as directly settable values via `PWR <value>` commands (real hardware does not accept these).
- Modelling abnormality standby (`05`).

## Decisions

### Decision 1 — New `PowerSequencer` class in `projector/power.py`

All timed transition logic is isolated in a new `PowerSequencer` class rather than being added to `ProjectorState` or `engine.py`.

**Rationale:** `handle_command` is designed as a pure, synchronous function. Introducing asyncio tasks there would break its contract and complicate testing. `ProjectorState` is a plain data container; it should remain free of coroutines. A separate collaborator keeps concerns separated and is easy to unit-test with a mocked state and short delays.

`PowerSequencer` owns an `asyncio.Task` (or `None`) for the in-flight transition. It exposes:
- `request_on(state, model)` → schedules `00`/`04` → `02` → `01`; returns `True` if started, `False` if rejected.
- `request_off(state, model)` → schedules `01` → `03` → `00`/`04`; returns `True` if started, `False` if rejected.
- `cancel()` → cancels any in-flight task synchronously (for model reload).
- `is_transitioning` → bool property used by the engine/keybinding.

**Alternative considered:** Storing the task on `ProjectorState`. Rejected because it mixes async lifecycle management into a data class and makes testing harder.

### Decision 2 — Engine receives an optional `PowerSequencer`; rejects mid-transition `PWR` commands

`handle_command` gains an optional `power_sequencer: PowerSequencer | None = None` parameter. When the sequencer is present:
- `PWR ON` → rejected with `ERR` unless current state is `00`/`04`.
- `PWR OFF` → rejected with `ERR` unless current state is `01`.
- On acceptance, the sequencer is invoked and the engine returns `\r:` immediately (the state machine progresses asynchronously).

When no sequencer is supplied (unit tests, serial transport without async context), the old synchronous behaviour is preserved.

**Alternative considered:** Checking the state inside the engine without a sequencer reference. Rejected because the engine cannot schedule async transitions without some handle to the event loop, and optional injection is the cleanest boundary.

### Decision 3 — Warmup and cooldown durations extracted from `executionTimes` in `ModelDef`

`ModelDef` gains two new fields: `warmup_seconds: float` and `cooldown_seconds: float`.

The JSON `executionTimes` array is scanned in `_load_json_model`:
- The first entry with `item == "PWR ON"` supplies warmup duration (e.g. `"30 seconds"` → `30.0`).
- The first entry with `item == "PWR OFF"` and `condition == "Normal"` supplies cooldown duration.
- Fallback defaults: `warmup_seconds = 5.0`, `cooldown_seconds = 3.0` (short for developer convenience).

**Alternative considered:** Hardcoding durations per model. Rejected because duration data already exists in the JSON files.

### Decision 4 — Communication standby (`04`) support detected from model `PWR?` enum values

`ModelDef` gains a boolean field `supports_comms_standby: bool`. It is set to `True` if the `PWR?` query command's `enumValues` list contains an entry with `code == "04"`.

The standby-target state after cooldown is then `"04"` if `supports_comms_standby` else `"00"`.

### Decision 5 — Initial `PWR` value stays `01` (Normal)

The emulator starts with `PWR` set to `"01"` (Normal / lamp on), matching the existing model default. No startup override is needed. This keeps the out-of-box experience simple: the emulator is immediately "ready" and clients can query or control it without first triggering a warmup sequence.

### Decision 6 — TUI `p` keybinding cycles states instantly, bypassing transition delays

`action_toggle_power` in `ui/app.py` cycles the `PWR` value through the state sequence — `00`/`04` → `02` → `01` → `03` → `00`/`04` — by writing the next state directly to `ProjectorState` without going through the `PowerSequencer`. Any in-flight sequencer task is cancelled first so the instant jump takes effect cleanly.

This lets operators reach any desired state in one or two key presses without waiting for warmup or cooldown delays. The `PowerSequencer` is still the path for protocol-level `PWR ON` / `PWR OFF` commands received from clients.

The `PowerSequencer` instance is created in `main.py` alongside the shared `ProjectorState` and passed into both the transports (via the engine call sites) and the TUI.

## Risks / Trade-offs

- [Risk] Transports other than the TUI keybinding may not have access to the sequencer → **Mitigation:** All transport `handle_command` call sites in `transports/` receive the sequencer. The sequencer is constructed once in `main.py` and injected everywhere.
- [Risk] asyncio task leaks on rapid model reload → **Mitigation:** `sequencer.cancel()` is called at the start of the model-reload path in `ui/app.py` before state is replaced.
- [Risk] Tests that assert immediate `PWR` state changes break → **Mitigation:** `handle_command` without a sequencer retains old synchronous behaviour; existing tests are unaffected. New tests cover sequencer behaviour directly.
- [Trade-off] Short default delays (5 s warmup, 3 s cooldown) diverge from real hardware. This is intentional for developer usability; operators who want realistic timing can be expected to accept the mismatch.
