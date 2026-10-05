"""Persistent settings stored as JSON in the user's config folder."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path

DEFAULT_AGENDA = """\
# One interval per line: name, then a length (50m, 1h30m, 45s, or a bare number = minutes)
Focus 25m
Break 5m
Focus 25m
Break 5m
Focus 25m
Long break 15m
Focus 25m
"""


def config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = base / "Timetable"
    path.mkdir(parents=True, exist_ok=True)
    # One-time carry-over of settings from the app's earlier name.
    old, new = base / "TimelineTimer" / "settings.json", path / "settings.json"
    if old.exists() and not new.exists():
        try:
            new.write_bytes(old.read_bytes())
        except OSError:
            pass
    return path


@dataclass
class Settings:
    dock: str = "top"              # "top" or "bottom"
    margin: int = 0                # px from the screen edge
    opacity: float = 0.88          # full-mode background opacity, 0.0 (clear) to 1.0
    compact_opacity: float = 0.0   # compact-mode background opacity, 0.0 (clear) to 1.0
    accent: str = "#2dd4bf"        # progress and playhead colour
    compact: bool = False
    compact_label_len: int = 14    # characters before "..." in compact mode
    show_passed: bool = True
    show_remaining: bool = False
    click_through: bool = True     # True = mouse passes through the HUD
    keep_on_top: bool = True
    warn_seconds: int = 30         # pulse the countdown in the last N seconds, 0 = off
    ding_enabled: bool = True
    volume: float = 0.7
    sound_file: str = ""           # optional custom ding (.wav)
    autostart: bool = False
    agenda: str = DEFAULT_AGENDA   # legacy (v0.1): only used once to create the first session

    @classmethod
    def load(cls) -> "Settings":
        path = config_dir() / "settings.json"
        s = cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return s
        known = {f.name for f in fields(cls)}
        for key, value in data.items():
            if key in known:
                setattr(s, key, value)
        return s

    def save(self) -> None:
        path = config_dir() / "settings.json"
        try:
            path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass
