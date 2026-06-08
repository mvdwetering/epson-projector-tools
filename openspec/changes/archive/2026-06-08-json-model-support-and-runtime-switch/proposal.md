## Why

The emulator currently depends on YAML model definitions and startup-only model selection. New model data is now generated as JSON from Epson workbook extracts, and operators need to switch models from the emulator UI while preserving predictable protocol behavior.

Without this change:
- model data has to be duplicated/transcoded into YAML,
- command metadata from workbook extraction (sources, IR codes, connectivity) is underused,
- runtime model exploration and validation are slower because emulator restart is manual,
- state table ordering is noisy for large command sets.

## What Changes

- Replace YAML model loading with JSON-only model loading.
- Parse command capabilities from JSON command rows into effective command behavior used by the engine.
- Add model metadata support in runtime model structures:
  - source list (for `SOURCELIST`/`SOURCELISTA` responses and `SOURCE` parameter validation),
  - IR codes (for `KEY` operand validation),
  - connectivity flags (for UI indication only).
- Add emulator TUI model switch flow that performs a safe internal restart (stop transports, reload model/state, restart transports).
- Update state table ordering:
  - fixed pinned commands first (`PWR`, `SOURCE`, `SNO`, `LAMP`, `KEY` when present),
  - up to 6 recent active commands,
  - remaining commands alphabetically.
- Keep transport support informational only in UI: unsupported status appears inline on the same transport row; no extra protocol-box lines are added.

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `model-definition`: move to JSON-only model format and include extracted metadata used by runtime.
- `escvp21-engine`: derive source-related command behavior from model metadata (`SOURCELIST`/`SOURCELISTA` responses plus `SOURCE` validation), validate KEY against IR codes, and constrain INC/DEC to decimal single-parameter commands.
- `tui`: support runtime model switching with restart semantics and prioritized state ordering with recent activity tracking.

## Impact

- Affected specs:
  - `openspec/specs/model-definition/spec.md`
  - `openspec/specs/escvp21-engine/spec.md`
  - `openspec/specs/tui/spec.md`
- Affected code (expected): `projector/model.py`, `projector/state.py` (if ordering hooks needed), `projector/engine.py`, `main.py`, `ui/app.py`.
- No transport protocol framing changes; transport capability differences are UI indicators only in this milestone.