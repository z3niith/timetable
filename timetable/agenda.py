"""Agenda parsing: one interval per line, e.g. ``Focus 50m`` or ``Break 10m``."""

from __future__ import annotations

import re
from dataclasses import dataclass

_UNIT_SECONDS = {"h": 3600, "hr": 3600, "m": 60, "min": 60, "s": 1, "sec": 1}
_PART = re.compile(r"(\d+(?:\.\d+)?)\s*(hr|h|min|m|sec|s)(?![a-zA-Z])", re.IGNORECASE)
_LINE = re.compile(
    r"^(?P<name>.*?)(?:\s+|^)"
    r"(?P<dur>(?:\d+(?:\.\d+)?\s*(?:hr|h|min|m|sec|s)(?![a-zA-Z])\s*)+|\d+(?:\.\d+)?)\s*$",
    re.IGNORECASE,
)
_BREAK_WORDS = ("break", "rest", "lunch", "pause")


@dataclass
class Item:
    name: str
    seconds: float

    @property
    def is_break(self) -> bool:
        return self.name.strip().lower().startswith(_BREAK_WORDS)


def parse_duration(text: str) -> float | None:
    """'1h30m' -> 5400, '50m' -> 3000, '45s' -> 45, bare '10' -> 600 (minutes)."""
    text = text.strip()
    parts = _PART.findall(text)
    if parts:
        return sum(float(n) * _UNIT_SECONDS[u.lower()] for n, u in parts)
    try:
        return float(text) * 60
    except ValueError:
        return None


def parse_agenda(text: str) -> list[Item]:
    """Parse the agenda text. Lines without a valid duration are skipped."""
    items: list[Item] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE.match(line)
        if not m:
            continue
        seconds = parse_duration(m.group("dur"))
        if not seconds or seconds <= 0:
            continue
        items.append(Item(m.group("name").strip() or "Interval", seconds))
    return items


def format_clock(seconds: float) -> str:
    """Countdown style: 05:00, or 1:05:00 when an hour or more."""
    s = max(0, int(round(seconds)))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def format_short(seconds: float) -> str:
    """Compact duration label: 5m, 1h, 1h30m, 45s."""
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h{m}m" if m else f"{h}h"
    if m:
        return f"{m}m" if not sec else f"{m}m{sec}s"
    return f"{sec}s"
