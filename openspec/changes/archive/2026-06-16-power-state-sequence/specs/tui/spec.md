## ADDED Requirements

### Requirement: Power key cycles through all power states instantly
The emulator TUI `p` keybinding SHALL advance `PWR` to the next state in the cycle — `00`/`04` → `02` → `01` → `03` → `00`/`04` — immediately, without waiting for warmup or cooldown delays. Any in-flight sequencer transition SHALL be cancelled before applying the instant state change.

#### Scenario: Advance from standby to warmup
- **WHEN** operator presses `p` and current `PWR` is `00` or `04`
- **THEN** `PWR` is set to `02` immediately

#### Scenario: Advance from warmup to normal
- **WHEN** operator presses `p` and current `PWR` is `02`
- **THEN** `PWR` is set to `01` immediately

#### Scenario: Advance from normal to cooldown
- **WHEN** operator presses `p` and current `PWR` is `01`
- **THEN** `PWR` is set to `03` immediately

#### Scenario: Advance from cooldown to standby
- **WHEN** operator presses `p` and current `PWR` is `03`
- **THEN** `PWR` is set to `00` or `04` (model's standby state) immediately

#### Scenario: In-flight sequencer task cancelled on key press
- **WHEN** operator presses `p` while a sequencer transition is running
- **THEN** the in-flight task is cancelled before the instant state change is applied

### Requirement: In-flight transition cancelled on model reload
The emulator TUI SHALL cancel any in-flight `PowerSequencer` transition before replacing state and model on a model switch.

#### Scenario: Transition cancelled before model reload
- **WHEN** the operator triggers a model switch while a warmup or cooldown is in progress
- **THEN** the sequencer is cancelled before state is replaced, preventing stale `PWR` writes after reload
