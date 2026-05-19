## ADDED Requirements

### Requirement: Preset storage location
The system SHALL store presets in a YAML file at the platform-appropriate user config directory, resolved via `platformdirs.user_config_dir("epson_terminal")`. The file SHALL be named `presets.yaml`. The directory SHALL be created automatically if it does not exist.

#### Scenario: Linux path
- **WHEN** the terminal runs on Linux
- **THEN** presets are stored at `~/.config/epson_terminal/presets.yaml`

#### Scenario: Windows path
- **WHEN** the terminal runs on Windows
- **THEN** presets are stored at `%APPDATA%\Local\epson_terminal\presets.yaml`

#### Scenario: Auto-create directory
- **WHEN** the config directory does not exist and a preset is saved
- **THEN** the directory is created and the file is written without error

---

### Requirement: Preset schema
Each preset SHALL be a named record containing: `name` (string, unique key), `protocol` (one of `serial`, `vpnet`, `http`), `host` (string), `port` (integer), `password` (string, may be empty). Presets SHALL be stored as an ordered list under a top-level `presets:` key.

#### Scenario: Valid preset file
- **WHEN** `presets.yaml` contains a preset with all required fields
- **THEN** `load_presets()` returns a list containing that preset as a dict

#### Scenario: Missing file
- **WHEN** `presets.yaml` does not exist
- **THEN** `load_presets()` returns an empty list without raising an error

#### Scenario: Malformed YAML
- **WHEN** `presets.yaml` contains invalid YAML
- **THEN** `load_presets()` returns an empty list and prints a warning to stderr

---

### Requirement: Save preset
The system SHALL provide a `save_preset(preset: dict)` operation that adds a new preset or overwrites an existing preset with the same name (case-sensitive), preserving the order of existing presets (the updated entry stays at its original position; new entries are appended).

#### Scenario: Add new preset
- **WHEN** `save_preset({"name": "office", ...})` is called and no preset named "office" exists
- **THEN** the preset is appended to the list and written to disk

#### Scenario: Overwrite existing preset
- **WHEN** `save_preset({"name": "office", "host": "10.0.0.1", ...})` is called and a preset named "office" already exists at index 1
- **THEN** the preset at index 1 is replaced in-place and the file is rewritten

---

### Requirement: Delete preset
The system SHALL provide a `delete_preset(name: str)` operation that removes the preset with the given name. If no preset with that name exists, the operation SHALL be a no-op.

#### Scenario: Delete existing preset
- **WHEN** `delete_preset("office")` is called and "office" exists
- **THEN** the preset is removed and the file is rewritten

#### Scenario: Delete non-existent preset
- **WHEN** `delete_preset("unknown")` is called
- **THEN** no error is raised and the file is unchanged

---

### Requirement: Find preset by name
The system SHALL provide a `find_preset(name: str) -> dict | None` operation that returns the preset dict for the given name, or `None` if not found.

#### Scenario: Found
- **WHEN** `find_preset("living-room")` is called and that preset exists
- **THEN** the preset dict is returned

#### Scenario: Not found
- **WHEN** `find_preset("unknown")` is called
- **THEN** `None` is returned
