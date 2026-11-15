"""Keeps the HUD above other windows on Windows.

Qt's "stay on top" flag is only applied once. Windows then lets other top-most windows, the taskbar,
or a window that was just activated sit above it. Re-asserting the top-most state every second
puts the HUD back on top without stealing focus. Exclusive-fullscreen games cannot be drawn over;
borderless-windowed mode works.
"""

from __future__ import annotations

import sys

HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

TOPMOST_FLAGS = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW


def _user32():
    import ctypes

    return ctypes.windll.user32


def raise_topmost(hwnd: int, user32=None) -> bool:
    """Move the window to the top of the top-most band without activating it. Returns success."""
    if sys.platform != "win32" and user32 is None:
        return False
    try:
        user32 = user32 or _user32()
        return bool(user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, TOPMOST_FLAGS))
    except (OSError, AttributeError):
        return False


def mark_no_activate(hwnd: int, user32=None) -> None:
    """Make clicks on the HUD never take focus from the app you are working in."""
    if sys.platform != "win32" and user32 is None:
        return
    try:
        user32 = user32 or _user32()
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        wanted = style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
        if wanted != style:
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, wanted)
    except (OSError, AttributeError):
        pass
