"""Which monitor the HUD sits on, and where. Pure functions, so they are easy to test."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int


def screen_key(screen) -> str:
    """A stable name for a monitor, kept in settings. Falls back to its name alone."""
    serial = ""
    try:
        serial = screen.serialNumber() or ""
    except AttributeError:
        pass
    return f"{screen.name()}|{serial}" if serial else screen.name()


def pick_screen(screens: list, primary, wanted: str):
    """The chosen monitor if it is plugged in, otherwise the primary one."""
    if wanted:
        for screen in screens:
            if screen_key(screen) == wanted:
                return screen
        for screen in screens:  # same port, different serial reporting
            if screen.name() == wanted.split("|")[0]:
                return screen
    return primary or (screens[0] if screens else None)


def dock_rect(area: Rect, height: int, dock: str, margin: int) -> Rect:
    """Full-width bar along the top or bottom of the usable area (taskbar excluded)."""
    m = max(0, margin)
    height = max(1, min(height, area.h))
    y = area.y + m if dock == "top" else area.y + area.h - height - m
    return Rect(area.x, y, area.w, height)
