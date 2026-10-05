"""Global hotkeys (Windows). A click-through window never gets key presses,
so these are how you control the timer without touching it."""

from __future__ import annotations

import sys
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication

MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
WM_HOTKEY = 0x0312


class Hotkeys(QAbstractNativeEventFilter):
    def __init__(self) -> None:
        super().__init__()
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._next_id = 1
        self.enabled = sys.platform == "win32"
        if self.enabled:
            QCoreApplication.instance().installNativeEventFilter(self)

    def register(self, mods: int, vk: int, callback: Callable[[], None]) -> bool:
        if not self.enabled:
            return False
        import ctypes

        hk_id = self._next_id
        if not ctypes.windll.user32.RegisterHotKey(None, hk_id, mods | MOD_NOREPEAT, vk):
            return False  # another app already owns this combination
        self._callbacks[hk_id] = callback
        self._next_id += 1
        return True

    def unregister_all(self) -> None:
        if not self.enabled:
            return
        import ctypes

        for hk_id in self._callbacks:
            ctypes.windll.user32.UnregisterHotKey(None, hk_id)
        self._callbacks.clear()

    def nativeEventFilter(self, event_type, message):  # noqa: N802 (Qt naming)
        if self.enabled and bytes(event_type) == b"windows_generic_MSG":
            import ctypes
            from ctypes import wintypes

            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam in self._callbacks:
                self._callbacks[msg.wParam]()
                return True, 0
        return False, 0
