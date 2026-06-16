## ADDED Requirements

### Requirement: Power state transitions through correct sequence
The `PowerSequencer` SHALL advance the `PWR` state through the correct hardware sequence with configurable delays rather than jumping directly to the target value.

#### Scenario: Power-on sequence
- **WHEN** a power-on transition is requested and current `PWR` is `00` or `04`
- **THEN** `PWR` is set to `02` (warmup) immediately, then after the warmup delay set to `01` (normal)

#### Scenario: Power-off sequence
- **WHEN** a power-off transition is requested and current `PWR` is `01`
- **THEN** `PWR` is set to `03` (cooldown) immediately, then after the cooldown delay set to `00` or `04` (standby)

#### Scenario: Cooldown target is communication standby when model supports it
- **WHEN** a power-off transition completes and the active model's `PWR?` enum includes code `04`
- **THEN** the final `PWR` state after cooldown is `04`

#### Scenario: Cooldown target is standby when model does not support communication standby
- **WHEN** a power-off transition completes and the active model's `PWR?` enum does not include code `04`
- **THEN** the final `PWR` state after cooldown is `00`

### Requirement: Power-on rejected during transition
The `PowerSequencer` SHALL reject a power-on request if a transition is already in progress.

#### Scenario: Power-on rejected during warmup
- **WHEN** `PWR ON` is requested and current `PWR` is `02`
- **THEN** the request is rejected and `PWR` state is unchanged

#### Scenario: Power-on rejected during cooldown
- **WHEN** `PWR ON` is requested and current `PWR` is `03`
- **THEN** the request is rejected and `PWR` state is unchanged

### Requirement: Power-off rejected during transition
The `PowerSequencer` SHALL reject a power-off request if a transition is already in progress or the projector is already in standby.

#### Scenario: Power-off rejected during warmup
- **WHEN** `PWR OFF` is requested and current `PWR` is `02`
- **THEN** the request is rejected and `PWR` state is unchanged

#### Scenario: Power-off rejected during cooldown
- **WHEN** `PWR OFF` is requested and current `PWR` is `03`
- **THEN** the request is rejected and `PWR` state is unchanged

#### Scenario: Power-off rejected when already in standby
- **WHEN** `PWR OFF` is requested and current `PWR` is `00` or `04`
- **THEN** the request is rejected and `PWR` state is unchanged

### Requirement: Transition durations sourced from model
The `PowerSequencer` SHALL use warmup and cooldown durations derived from the active model's `executionTimes` data.

#### Scenario: Warmup duration from model
- **WHEN** the model's `executionTimes` contains an entry with `item == "PWR ON"`
- **THEN** that entry's time value (in seconds) is used as the warmup delay

#### Scenario: Cooldown duration from model
- **WHEN** the model's `executionTimes` contains an entry with `item == "PWR OFF"` and `condition == "Normal"`
- **THEN** that entry's time value (in seconds) is used as the cooldown delay

#### Scenario: Default warmup applied when not in model
- **WHEN** the model's `executionTimes` does not contain a `PWR ON` entry
- **THEN** a default warmup delay of 5 seconds is used

#### Scenario: Default cooldown applied when not in model
- **WHEN** the model's `executionTimes` does not contain a normal `PWR OFF` entry
- **THEN** a default cooldown delay of 3 seconds is used

### Requirement: In-flight transition cancelled on model reload
The `PowerSequencer` SHALL expose a `cancel()` method that terminates any in-flight asyncio transition task immediately.

#### Scenario: Cancel aborts warmup task
- **WHEN** `cancel()` is called while a warmup task is running
- **THEN** the task is cancelled and no further `PWR` state changes occur

#### Scenario: Cancel is safe when idle
- **WHEN** `cancel()` is called and no transition is in progress
- **THEN** no error occurs

### Requirement: Emulator starts in Normal status
The emulator SHALL initialize `PWR` to `01` (Normal / lamp on) at startup.

#### Scenario: Initial power state is Normal
- **WHEN** the emulator starts
- **THEN** initial `PWR` value is `01`
