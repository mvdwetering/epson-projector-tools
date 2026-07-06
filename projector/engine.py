from __future__ import annotations

import re
from typing import TYPE_CHECKING

from projector.model import ModelDef
from projector.state import ProjectorState

if TYPE_CHECKING:
    from projector.power import PowerSequencer

# Matches "CMD value" (SET) or "CMD?" (GET)
_SET_RE = re.compile(r"^(?P<cmd>[A-Za-z0-9]+) (?P<val>.*)$")
_GET_RE = re.compile(r"^(?P<cmd>[A-Za-z0-9]+)\?$")

_OK = ":"
_ERR = "ERR\r:"

# Common IR-key mappings applied regardless of ingress transport.
_KEY_DIRECT_SET: dict[str, tuple[str, str]] = {
    "A1": ("PWR", "ON"),   # Power ON
    "6C": ("PWR", "OFF"),   # Power OFF
    "40": ("SOURCE", "A0"),  # HDMI2
    "4D": ("SOURCE", "30"),  # HDMI1
    "44": ("SOURCE", "10"),  # PC
    "46": ("SOURCE", "40"),  # Video
    "56": ("VOL", "INC"),    # Volume up
    "57": ("VOL", "DEC"),    # Volume down
}


def handle_command(
    state: ProjectorState,
    model: ModelDef,
    cmd_str: str,
    power_sequencer: "PowerSequencer | None" = None,
) -> str:
    """
    Process a single ESC/VP21 command string and return the response.

    This is a pure function: it mutates `state` but performs no I/O.
    Response format:
      - GET success : "CMD=value\\r:"
      - SET / null  : ":"
      - Error       : "ERR\\r:"
    """
    line = cmd_str.strip()

    # Null command — heartbeat / keepalive
    if not line:
        return _OK

    # Try GET
    m = _GET_RE.match(line)
    if m:
        return _handle_get(state, model, m.group("cmd"))

    # Try SET
    m = _SET_RE.match(line)
    if m:
        return _handle_set(state, model, m.group("cmd"), m.group("val"), power_sequencer)

    return _ERR


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _handle_get(state: ProjectorState, model: ModelDef, cmd: str) -> str:
    if cmd in {"SOURCELIST", "SOURCELISTA"}:
        cmd_def = model.commands.get(cmd)
        if cmd_def is None or not cmd_def.readable:
            return _ERR
        entries: list[str] = []
        for src in model.non_cyclic_sources():
            entries.append(src.code)
            entries.append(src.name)
        return f"{cmd}={' '.join(entries)}\r:"

    cmd_def = model.commands.get(cmd)
    if cmd_def is None or not cmd_def.readable:
        return _ERR
    value = state.get(cmd)
    if value is None:
        return _ERR
    return f"{cmd}={value}\r:"


def _handle_set(state: ProjectorState, model: ModelDef, cmd: str, value: str, power_sequencer: "PowerSequencer | None" = None) -> str:
    cmd_def = model.commands.get(cmd)
    if cmd_def is None or not cmd_def.writable:
        return _ERR

    # INIT is accepted on any writable command but makes no state change
    if value == "INIT":
        return _OK

    # INC / DEC on numeric commands
    if value in ("INC", "DEC"):
        if not cmd_def.inc_dec or not cmd_def.decimal_single_param:
            return _ERR
        current = state.get(cmd)
        if current is None:
            return _ERR
        try:
            int_val = int(current)
        except ValueError:
            return _ERR
        delta = 1 if value == "INC" else -1
        new_val = int_val + delta
        if cmd_def.range is not None:
            new_val = max(cmd_def.range[0], min(cmd_def.range[1], new_val))
        state.set(cmd, str(new_val))
        return _OK

    if cmd == "SOURCE" and value not in model.source_codes():
        return _ERR

    if cmd == "KEY":
        if value not in model.ir_codes:
            return _ERR

        # KEY command can trigger side-effect command dispatch shared by all transports.
        mapped = _map_key_to_command(state, value)
        if mapped is not None:
            mapped_cmd, mapped_value = mapped
            return _handle_set(state, model, mapped_cmd, mapped_value, power_sequencer)

    # notify_only commands (e.g. KEY): acknowledge but don't store
    if cmd_def.notify_only:
        return _OK

    # Apply set_map if defined (e.g. PWR: ON→"01", OFF→"00")
    if cmd_def.set_map is not None:
        if value not in cmd_def.set_map:
            return _ERR
        mapped = cmd_def.set_map[value]
    elif cmd_def.set_values is not None:
        if value not in cmd_def.set_values:
            return _ERR
        mapped = value
    else:
        mapped = value

    # Delegate PWR transitions to the sequencer when available
    if cmd == "PWR" and power_sequencer is not None:
        if mapped == "01":
            return _OK if power_sequencer.request_on(state, model) else _ERR
        if mapped == "00":
            return _OK if power_sequencer.request_off(state, model) else _ERR

    if not state.set(cmd, mapped):
        return _ERR
    return _OK


def _map_key_to_command(state: ProjectorState, ir_code: str) -> tuple[str, str] | None:
    if ir_code == "3B":
        return ("PWR", "OFF" if state.get("PWR") == "01" else "ON")

    if ir_code == "3E":
        return ("MUTE", "OFF" if state.get("MUTE") == "ON" else "ON")

    mapped = _KEY_DIRECT_SET.get(ir_code)
    if mapped is None:
        return None
    return mapped
