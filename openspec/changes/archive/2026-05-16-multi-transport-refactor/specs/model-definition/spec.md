## ADDED Requirements

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

#### Scenario: Model parsed into dataclasses
- **WHEN** a valid YAML model file is loaded
- **THEN** a `ModelDef` dataclass is returned with a dict of `CommandDef` dataclasses

#### Scenario: Invalid model file
- **WHEN** a YAML file is missing required fields or has invalid types
- **THEN** loading SHALL raise a `ValueError` at startup with a descriptive message

### Requirement: Model parsed into dataclasses
`ModelDef` and `CommandDef` SHALL be implemented as Python `dataclasses`. Validation SHALL be done in a `from_dict()` class method; no third-party validation library is used.

### Requirement: Model selected at startup
The active model SHALL be selected by CLI argument (model name or file path). The default SHALL be `eh_tw3200`.

#### Scenario: Default model
- **WHEN** no model argument is provided
- **THEN** `models/eh_tw3200.yaml` is loaded

#### Scenario: Explicit model argument
- **WHEN** `--model eh_tw9400` is passed
- **THEN** `models/eh_tw9400.yaml` is loaded

### Requirement: EH-TW3200 model file
A complete model definition file for the EH-TW3200 SHALL exist at `models/eh_tw3200.yaml`, covering all commands currently supported in the original `server.py`.

#### Scenario: All legacy commands present
- **WHEN** `models/eh_tw3200.yaml` is loaded
- **THEN** commands PWR, SOURCE, ASPECT, LUMINANCE, BRIGHT, CONTRAST, CMODE, MUTE, HREVERSE, VREVERSE, LAMP, SNO and all others from original `server.py` are present
