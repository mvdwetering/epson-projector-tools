## MODIFIED Requirements

### Requirement: YAML model file format
Each model SHALL be defined in a YAML file under `models/` with the following structure:
- `name`: human-readable model name (string)
- `commands`: mapping of command names to command definitions
  - `default`: initial value (string)
  - `readable`: bool — command supports GET
  - `writable`: bool — command supports SET
  - `inc_dec`: bool (optional, default false) — command supports INC/DEC
  - `range`: [min, max] (optional) — valid integer range for inc/dec and set
  - `set_values`: list of strings (optional) — explicit accepted SET operands
  - `notify_only`: bool (optional, default false) — SET is acknowledged but not stored (e.g. `KEY`)

#### Scenario: Model parsed into dataclasses
- **WHEN** a valid YAML model file is loaded
- **THEN** a `ModelDef` dataclass is returned with a dict of `CommandDef` dataclasses

#### Scenario: Invalid model file
- **WHEN** a YAML file is missing required fields or has invalid types
- **THEN** loading SHALL raise a `ValueError` at startup with a descriptive message

### Requirement: EH-TW3200 model file
A complete model definition file for the EH-TW3200 SHALL exist at `models/eh_tw3200.yaml`, covering all supported ESC/VP21 commands. The volume command SHALL be named `VOL` (not `VOLUME`) to match the ESC/VP21 specification.

#### Scenario: VOL command present
- **WHEN** `models/eh_tw3200.yaml` is loaded
- **THEN** a command named `VOL` is present; no command named `VOLUME` exists

#### Scenario: All legacy commands present
- **WHEN** `models/eh_tw3200.yaml` is loaded
- **THEN** commands PWR, SOURCE, ASPECT, LUMINANCE, BRIGHT, CONTRAST, CMODE, MUTE, HREVERSE, VREVERSE, LAMP, SNO, VOL, KEY and all others are present
