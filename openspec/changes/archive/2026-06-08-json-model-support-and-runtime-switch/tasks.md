## 1. JSON Model Runtime

- [x] 1.1 Replace YAML model loading with JSON-only loading in startup and loader utilities.
- [x] 1.2 Parse model metadata (`sources`, `irCodes`, connectivity) into runtime `ModelDef` fields.
- [x] 1.3 Aggregate JSON command rows by command token into effective runtime command definitions with readable/writable/set constraints.
- [x] 1.4 Ensure unknown connectivity values (`null`) are treated as supported for UI indication logic.

## 2. Engine Behavior Updates

- [x] 2.1 Implement `SOURCELIST?` and `SOURCELISTA?` responses from model source metadata using identical payload behavior for now.
- [x] 2.2 Filter out cyclic source entries from both source-list responses.
- [x] 2.3 Validate `SOURCE` command operands against the same non-cyclic model source list used by `SOURCELIST`/`SOURCELISTA`.
- [x] 2.4 Validate `KEY` command operands against model `irCodes`.
- [x] 2.5 Restrict INC/DEC to decimal single-parameter commands and return ERR otherwise.
- [x] 2.6 Add/adjust engine tests for `VOL`-style decimal INC/DEC, mixed-parameter command rejection, source-list responses, SOURCE validation, and KEY validation.

## 3. TUI Runtime Model Switching

- [x] 3.1 Add a model selection action in emulator TUI that lists available JSON model files.
- [x] 3.2 Implement safe restart flow on model switch: stop transports, reload model+state, rebuild views, restart transports.
- [x] 3.3 Update title to selected filename or model name.
- [x] 3.4 Keep config/protocol box compact and place unsupported transport indicator inline on each transport row.
- [x] 3.5 Update state table ordering to pinned-first, then 6 recent active commands, then alphabetical remainder.

## 4. Validation And Regression

- [x] 4.1 Add/update tests for JSON loader validation and command aggregation behavior.
- [x] 4.2 Add/update TUI tests for model switch flow, inline unsupported indicators, and state ordering.
- [x] 4.3 Run targeted emulator, engine, and transport tests to verify no regressions in command handling or transport I/O.