from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import yaml
from platformdirs import user_config_dir

_CONFIG_DIR = Path(user_config_dir("epson_terminal"))
_PRESETS_FILE = _CONFIG_DIR / "presets.yaml"


def load_presets() -> list[dict]:
    """Return all saved presets, or [] on missing/invalid file."""
    if not _PRESETS_FILE.exists():
        return []
    try:
        with _PRESETS_FILE.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return []
        presets = data.get("presets", [])
        return [p for p in presets if isinstance(p, dict)]
    except Exception as exc:
        print(f"Warning: could not load presets from {_PRESETS_FILE}: {exc}", file=sys.stderr)
        return []


def _write_presets(presets: list[dict]) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with _PRESETS_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump({"presets": presets}, f, default_flow_style=False, allow_unicode=True)


def save_preset(preset: dict) -> None:
    """Add or overwrite a preset by name (preserves order of existing entries)."""
    presets = load_presets()
    name = preset["name"]
    for i, p in enumerate(presets):
        if p.get("name") == name:
            presets[i] = preset
            _write_presets(presets)
            return
    presets.append(preset)
    _write_presets(presets)


def delete_preset(name: str) -> None:
    """Remove a preset by name. No-op if not found."""
    presets = load_presets()
    new_presets = [p for p in presets if p.get("name") != name]
    if len(new_presets) != len(presets):
        _write_presets(new_presets)


def find_preset(name: str) -> Optional[dict]:
    """Return the preset dict for the given name, or None if not found."""
    for p in load_presets():
        if p.get("name") == name:
            return p
    return None
