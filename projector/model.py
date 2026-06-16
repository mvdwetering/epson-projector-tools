from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

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
    # True only for single-parameter decimal commands where INC/DEC is safe.
    decimal_single_param: bool = False

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
            decimal_single_param=bool(data.get("decimal_single_param", False)),
        )


@dataclass(frozen=True)
class Connectivity:
    rs232c: bool | None = None
    wired_lan: bool | None = None
    wireless_lan: bool | None = None
    usb_b: bool | None = None


@dataclass(frozen=True)
class SourceDef:
    code: str
    name: str
    source_label: str
    cyclic: bool = False


@dataclass
class ModelDef:
    name: str
    model_id: str = ""
    file_name: str = ""
    commands: dict[str, CommandDef] = field(default_factory=dict)
    sources: list[SourceDef] = field(default_factory=list)
    ir_codes: set[str] = field(default_factory=set)
    connectivity: Connectivity = field(default_factory=Connectivity)
    warmup_seconds: float = 5.0
    cooldown_seconds: float = 3.0
    supports_comms_standby: bool = False

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

    @property
    def standby_state(self) -> str:
        return "04" if self.supports_comms_standby else "00"

    def non_cyclic_sources(self) -> list[SourceDef]:
        return [src for src in self.sources if not src.cyclic]

    def source_codes(self) -> set[str]:
        return {src.code for src in self.non_cyclic_sources()}

    def serial_supported(self) -> bool:
        # Unknown connectivity means "assume supported".
        if self.connectivity.rs232c is None and self.connectivity.usb_b is None:
            return True
        return bool(self.connectivity.rs232c or self.connectivity.usb_b)

    def network_supported(self) -> bool:
        # Unknown connectivity means "assume supported".
        if (
            self.connectivity.wired_lan is None
            and self.connectivity.wireless_lan is None
        ):
            return True
        return bool(self.connectivity.wired_lan or self.connectivity.wireless_lan)


def _as_bool_or_none(value: object) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _normalize_token(token: str) -> str:
    token = token.strip().upper()
    if token.endswith("?"):
        token = token[:-1]
    return token


def _normalize_value_token(value: object) -> str:
    if isinstance(value, int):
        return str(value)
    return str(value).strip().upper()


def _is_cyclic_source(source_label: str, name: str) -> bool:
    text = f"{source_label} {name}".lower()
    return "change cyclic" in text


def _is_decimal_range(min_raw: str, max_raw: str) -> bool:
    return min_raw.isdigit() and max_raw.isdigit() and not (
        (len(min_raw) > 1 and min_raw.startswith("0"))
        or (len(max_raw) > 1 and max_raw.startswith("0"))
    )


def _extract_literal_set_operand(row: dict) -> str | None:
    set_cmd = row.get("setCommand")
    if not isinstance(set_cmd, str):
        return None
    parts = set_cmd.strip().split(maxsplit=1)
    if len(parts) != 2:
        return None
    placeholders = row.get("parameterPlaceholders") or []
    if placeholders:
        # Keep symbolic placeholders (x1/xx/etc.) out of literal operand sets.
        if any(re.fullmatch(r"x+\d*", str(ph).strip(), flags=re.IGNORECASE) for ph in placeholders):
            return None
        if len(placeholders) == 1:
            return str(placeholders[0]).strip().upper()
        return None
    return parts[1].strip().upper()


def _build_sources(data: dict) -> list[SourceDef]:
    sources: list[SourceDef] = []
    for item in data.get("sources", []):
        if not isinstance(item, dict):
            continue
        code_raw = item.get("code")
        if code_raw is None:
            continue
        code = _normalize_value_token(code_raw)
        name = str(item.get("name", "")).strip() or code
        source_label = str(item.get("sourceLabel", "")).strip()
        sources.append(
            SourceDef(
                code=code,
                name=name,
                source_label=source_label,
                cyclic=_is_cyclic_source(source_label, name),
            )
        )
    return sources


def _build_ir_codes(data: dict) -> set[str]:
    codes: set[str] = set()
    for item in data.get("irCodes", []):
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        if code is None:
            continue
        codes.add(_normalize_value_token(code))
    return codes


def _parse_execution_times(data: dict) -> tuple[float, float]:
    """Return (warmup_seconds, cooldown_seconds) parsed from executionTimes."""
    warmup = 5.0
    cooldown = 3.0
    for entry in data.get("executionTimes") or []:
        if not isinstance(entry, dict):
            continue
        item = entry.get("item", "")
        condition = entry.get("condition", "")
        time_str = str(entry.get("time", ""))
        try:
            seconds = float(time_str.split()[0])
        except (ValueError, IndexError):
            continue
        if item == "PWR ON" and warmup == 5.0:
            warmup = seconds
        elif item == "PWR OFF" and "Normal" in condition and cooldown == 3.0:
            cooldown = seconds
    return warmup, cooldown


def _aggregate_commands(data: dict, sources: list[SourceDef], ir_codes: set[str]) -> tuple[dict[str, CommandDef], bool]:
    rows = data.get("commands")
    if not isinstance(rows, list):
        raise ValueError("Model definition missing 'commands' list")

    grouped: dict[str, dict] = {}
    supports_comms_standby = False

    for row in rows:
        if not isinstance(row, dict):
            continue
        token_raw = row.get("commandToken")
        if not isinstance(token_raw, str) or not token_raw.strip():
            continue
        token = _normalize_token(token_raw)
        entry = grouped.setdefault(
            token,
            {
                "readable": False,
                "writable": False,
                "inc_dec": False,
                "set_values": set(),
                "set_map": {},
                "default": "00",
                "decimal_single_param": False,
                "range": None,
            },
        )

        can_set = bool(row.get("canSet", False))
        can_query = bool(row.get("canQuery", False))
        # In extracted JSON, query capability can be incomplete for commands that
        # are practically queried by clients (for example SOURCE?). Keep GET
        # support permissive for command tokens that can be set.
        entry["readable"] = entry["readable"] or can_query or can_set
        entry["writable"] = entry["writable"] or can_set

        literal_operand = _extract_literal_set_operand(row)
        if literal_operand:
            entry["set_values"].add(literal_operand)
            if token == "PWR" and literal_operand in {"ON", "OFF"}:
                entry["set_map"][literal_operand] = "01" if literal_operand == "ON" else "00"

        # Detect communication standby support from PWR? enum values
        if token == "PWR" and not can_set and can_query:
            for ev in row.get("enumValues") or []:
                if isinstance(ev, dict) and ev.get("code") == "04":
                    supports_comms_standby = True

        placeholders = row.get("parameterPlaceholders") or []
        ranges = row.get("parameterRanges") or []
        if (
            can_set
            and bool(row.get("incDecSupported", False))
            and len(placeholders) == 1
            and len(ranges) == 1
            and isinstance(ranges[0], dict)
        ):
            min_raw = str(ranges[0].get("min", "")).strip()
            max_raw = str(ranges[0].get("max", "")).strip()
            if _is_decimal_range(min_raw, max_raw):
                entry["inc_dec"] = True
                entry["decimal_single_param"] = True
                entry["range"] = (int(min_raw), int(max_raw))

    # SOURCE and KEY are explicitly constrained by model metadata.
    non_cyclic_codes = {src.code for src in sources if not src.cyclic}
    if "SOURCE" in grouped:
        grouped["SOURCE"]["set_values"] = set(non_cyclic_codes)
        grouped["SOURCE"]["readable"] = True
    if "KEY" in grouped:
        grouped["KEY"]["set_values"] = set(ir_codes)

    commands: dict[str, CommandDef] = {}
    for token, entry in grouped.items():
        default = ""
        if token == "PWR":
            default = "01"
        elif token == "SOURCE":
            default = sorted(entry["set_values"])[0] if entry["set_values"] else "00"
        elif token == "SNO":
            default = ""
        elif token == "LAMP":
            default = "1234"
        elif token in {"SOURCELIST", "SOURCELISTA"}:
            default = ""
        elif token == "KEY":
            default = ""
        else:
            default = entry["default"]

        commands[token] = CommandDef(
            default=default,
            readable=bool(entry["readable"]),
            writable=bool(entry["writable"]),
            inc_dec=bool(entry["inc_dec"]),
            range=entry["range"],
            set_values=sorted(entry["set_values"]) if entry["set_values"] else None,
            set_map=entry["set_map"] or None,
            notify_only=(token == "KEY"),
            decimal_single_param=bool(entry["decimal_single_param"]),
        )

    return commands, supports_comms_standby


def _generate_model_serial(model_id: str, model_name: str, file_name: str) -> str:
    # Deterministic, model-unique 11-char serial-like token.
    seed = f"{model_id}|{model_name}|{file_name}".encode("utf-8")
    digest = hashlib.sha1(seed).hexdigest().upper()
    return f"X{digest[:10]}"


def _load_json_model(path: Path) -> ModelDef:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Model file '{path}' must contain a JSON object")

    model_obj = data.get("model")
    if not isinstance(model_obj, dict):
        raise ValueError("Model definition missing required object 'model'")
    name = model_obj.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Model definition missing required field 'model.name'")

    connectivity_raw = model_obj.get("connectivity") or {}
    if not isinstance(connectivity_raw, dict):
        connectivity_raw = {}

    sources = _build_sources(data)
    ir_codes = _build_ir_codes(data)
    commands, supports_comms_standby = _aggregate_commands(data, sources, ir_codes)
    warmup_seconds, cooldown_seconds = _parse_execution_times(data)

    model_id = str(model_obj.get("id", "")).strip()
    serial_default = _generate_model_serial(model_id, name.strip(), path.name)
    if "SNO" not in commands:
        commands["SNO"] = CommandDef(
            default=serial_default,
            readable=True,
            writable=False,
        )
    else:
        # Always ensure SNO is readable, read-only, and model-unique.
        sno = commands["SNO"]
        sno.readable = True
        sno.writable = False
        sno.default = serial_default

    return ModelDef(
        name=name.strip(),
        model_id=model_id,
        file_name=path.name,
        commands=commands,
        sources=sources,
        ir_codes=ir_codes,
        connectivity=Connectivity(
            rs232c=_as_bool_or_none(connectivity_raw.get("rs232c")),
            wired_lan=_as_bool_or_none(connectivity_raw.get("wiredLan")),
            wireless_lan=_as_bool_or_none(connectivity_raw.get("wirelessLan")),
            usb_b=_as_bool_or_none(connectivity_raw.get("usbB")),
        ),
        warmup_seconds=warmup_seconds,
        cooldown_seconds=cooldown_seconds,
        supports_comms_standby=supports_comms_standby,
    )


def load_model(path: str | Path) -> ModelDef:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")
    if path.suffix.lower() != ".json":
        raise ValueError(
            f"Unsupported model format '{path.suffix or '<none>'}'. Only .json is supported."
        )
    return _load_json_model(path)
