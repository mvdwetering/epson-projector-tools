## MODIFIED Requirements

### Requirement: YAML model file format
Each model SHALL be defined in a JSON file under `models/` with the following structure:
- `model`: object with model identity fields (`id`, `name`, optional aliases/support headers) and `connectivity`.
- `commands`: list of command rows exported from workbook data.
- `sources`: list of source entries used by source-list commands.
- `irCodes`: list of IR key code entries used for `KEY` operand validation.

The runtime loader SHALL aggregate command rows into effective per-token command definitions used by the engine.

#### Scenario: Model parsed into dataclasses from JSON
- **WHEN** a valid JSON model file is loaded
- **THEN** a `ModelDef` dataclass is returned with aggregated command definitions and metadata (`sources`, `irCodes`, connectivity)

#### Scenario: Invalid JSON model file
- **WHEN** a JSON file is missing required sections or has incompatible types
- **THEN** loading SHALL raise a `ValueError` at startup with a descriptive message

#### Scenario: Unsupported model format
- **WHEN** a non-JSON model file is provided
- **THEN** startup SHALL fail with a clear unsupported format error

### Requirement: Model selected at startup
The active model SHALL be selected by CLI argument (model name or file path). The default SHALL resolve to a JSON model file.

#### Scenario: Default model
- **WHEN** no model argument is provided
- **THEN** the configured default JSON model in `models/` is loaded

#### Scenario: Explicit model argument
- **WHEN** `--model <name>` is passed without extension
- **THEN** `models/<name>.json` is loaded

#### Scenario: Explicit JSON path
- **WHEN** `--model /path/to/model.json` is passed
- **THEN** that file is loaded as the active model