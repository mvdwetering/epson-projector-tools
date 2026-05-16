from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class CommandDef:
    default: str
    readable: bool = True
    writable: bool = True
    inc_dec: bool = False
    range: Optional[tuple[int, int]] = None
    set_values: Optional[list[str]] = None
    # Maps accepted SET operand → stored value (e.g. ON→"01", OFF→"00")
    set_map: Optional[dict[str, str]] = None
    # SET is processed but value is not stored (e.g. KEY remote commands)
    notify_only: bool = False

    @classmethod
    def from_dict(cls, data: dict, name: str) -> "CommandDef":
        if "default" not in data:
            raise ValueError(f"Command '{name}' missing required field 'default'")
        raw_range = data.get("range")
        parsed_range = tuple(raw_range) if raw_range is not None else None
        if parsed_range is not None and len(parsed_range) != 2:
            raise ValueError(f"Command '{name}': range must have exactly 2 elements")
        return cls(
            default=str(data["default"]),
            readable=bool(data.get("readable", True)),
            writable=bool(data.get("writable", True)),
            inc_dec=bool(data.get("inc_dec", False)),
            range=parsed_range,
            set_values=data.get("set_values"),
            set_map=data.get("set_map"),
            notify_only=bool(data.get("notify_only", False)),
        )


@dataclass
class ModelDef:
    name: str
    commands: dict[str, CommandDef] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "ModelDef":
        if "name" not in data:
            raise ValueError("Model definition missing required field 'name'")
        if "commands" not in data or not isinstance(data["commands"], dict):
            raise ValueError("Model definition missing 'commands' mapping")
        commands = {
            cmd_name: CommandDef.from_dict(cmd_data, cmd_name)
            for cmd_name, cmd_data in data["commands"].items()
        }
        return cls(name=data["name"], commands=commands)


def load_model(path: str | Path) -> ModelDef:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Model file '{path}' must contain a YAML mapping")
    return ModelDef.from_dict(data)
