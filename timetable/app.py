"""Wires the engine, HUD, tray icon, hotkeys and sound together."""

from __future__ import annotations

import sys

from PySide6.QtCore import QDir, QLockFile, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from . import __version__
from .agenda import format_clock, parse_agenda
from .dialogs import AgendaDialog, SettingsDialog
from .engine import State, TimerEngine
from .hotkeys import MOD_ALT, MOD_CONTROL, Hotkeys
from .hud import Hud
from .settings import Settings
from .sound import SoundPlayer


def make_icon(accent: str) -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(8, 14, 26))
    p.setPen(Qt.NoPen)
    p.drawEllipse(2, 2, 60, 60)
    p.setPen(QPen(QColor(accent), 6, Qt.SolidLine, Qt.RoundCap))
    p.drawArc(12, 12, 40, 40, 90 * 16, -250 * 16)
    p.setPen(QPen(QColor(200, 210, 224), 4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(32, 32, 32, 20)
    p.end()
    return QIcon(pm)


def set_autostart(enabled: bool) -> None:
    if sys.platform != "win32":
        return
    import winreg

    cmd = f'"{sys.executable}"' if getattr(sys, "frozen", False) else f'"{sys.executable.replace("python.exe", "pythonw.exe")}" -m timetable'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, "Timetable", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "Timetable")
            except FileNotFoundError:
                pass


class Controller:
    def __init__(self, app: QApplication):
        self.app = app
        self.s = Settings.load()
        self.engine = TimerEngine(parse_agenda(self.s.agenda))
        self.sound = SoundPlayer(self.s)
        self.engine.on_interval_end = lambda item, last: self.sound.play("done" if last else "ding")
        self.hud = Hud(self.engine, self.s)
        self.hud.action.connect(self.do)
        self.agenda_dlg = self.settings_dlg = None
        self._build_tray()
        self._register_hotkeys()
        t = QTimer(app, interval=1000)
        t.timeout.connect(self._refresh_tooltip)
        t.start()
        self._refresh_tooltip()

    # -- actions -----------------------------------------------------------
    def do(self, name: str) -> None:
        e = self.engine
        if name == "toggle":
            e.toggle()
        elif name == "restart":
            e.restart()
        elif name == "skip":
            e.skip()
        elif name == "plus":
            e.adjust(60)
        elif name == "minus":
            e.adjust(-60)
        elif name == "compact":
            self.s.compact = not self.s.compact
            self._window_changed()
        elif name == "lock":
            self.s.click_through = not self.s.click_through
            self._window_changed()
        elif name == "agenda":
            self.show_agenda()
        elif name == "settings":
            self.show_settings()
        elif name == "quit":
            self.quit()
        self.hud.update()

    def _window_changed(self) -> None:
        self.s.save()
        self.hud.apply_window_state()
        self.hud.update()

    def show_agenda(self) -> None:
        if self.agenda_dlg is None:
            self.agenda_dlg = AgendaDialog(self.s.agenda)
            self.agenda_dlg.changed.connect(self._agenda_edited)
        self.agenda_dlg.set_text(self.s.agenda)
        self._raise(self.agenda_dlg)

    def _agenda_edited(self, text: str) -> None:
        self.s.agenda = text
        self.engine.set_items(parse_agenda(text))
        self.s.save()
        self.hud.update()

    def show_settings(self) -> None:
        if self.settings_dlg is None:
            self.settings_dlg = SettingsDialog(self.s, lambda: self.sound.play("ding", force=True))
            self.settings_dlg.changed.connect(self._settings_changed)
        self._raise(self.settings_dlg)

    def _settings_changed(self) -> None:
        self.s.save()
        self.sound.reload()
        set_autostart(self.s.autostart)
        self.tray.setIcon(make_icon(self.s.accent))
        self.hud.apply_window_state()
        self.hud.update()

    @staticmethod
    def _raise(dlg) -> None:
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    # -- tray --------------------------------------------------------------
    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(make_icon(self.s.accent), self.app)
        menu = QMenu()
        self.act_toggle = menu.addAction("Start", lambda: self.do("toggle"))
        menu.addAction("Restart", lambda: self.do("restart"))
        menu.addAction("Skip interval", lambda: self.do("skip"))
        menu.addSeparator()
        self.act_compact = self._checkable(menu, "Compact mode", self.s.compact, "compact")
        self.act_unlock = self._checkable(menu, "Interactive mode (unlock)", not self.s.click_through, "lock")
        menu.addAction("Edit agenda...", lambda: self.do("agenda"))
        menu.addAction("Settings...", lambda: self.do("settings"))
        menu.addSeparator()
        menu.addAction("Quit", lambda: self.do("quit"))
        menu.aboutToShow.connect(self._sync_menu)
        self.menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_clicked)
        self.tray.show()

    def _checkable(self, menu: QMenu, text: str, checked: bool, action: str) -> QAction:
        act = menu.addAction(text)
        act.setCheckable(True)
        act.setChecked(checked)
        act.triggered.connect(lambda: self.do(action))
        return act

    def _sync_menu(self) -> None:
        self.act_toggle.setText("Pause" if self.engine.state is State.RUNNING else "Start")
        self.act_compact.setChecked(self.s.compact)
        self.act_unlock.setChecked(not self.s.click_through)

    def _tray_clicked(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self.do("toggle")
        elif reason == QSystemTrayIcon.DoubleClick:
            self.do("lock")

    def _refresh_tooltip(self) -> None:
        e = self.engine
        if e.state is State.FINISHED:
            tip = "Timetable: done"
        elif e.current:
            tip = f"Timetable: {e.current.name} {format_clock(e.remaining)}"
            if e.state is not State.RUNNING:
                tip += " (paused)" if e.state is State.PAUSED else " (ready)"
        else:
            tip = "Timetable"
        self.tray.setToolTip(tip)

    # -- hotkeys -----------------------------------------------------------
    def _register_hotkeys(self) -> None:
        self.hotkeys = Hotkeys()
        mod = MOD_CONTROL | MOD_ALT
        for vk, action in (
            (0x20, "toggle"),   # Space
            (0x27, "skip"),     # Right arrow
            (ord("R"), "restart"),
            (0x26, "plus"),     # Up arrow
            (0x28, "minus"),    # Down arrow
            (ord("C"), "compact"),
            (ord("L"), "lock"),
            (ord("E"), "agenda"),
        ):
            self.hotkeys.register(mod, vk, lambda a=action: self.do(a))

    def quit(self) -> None:
        self.hotkeys.unregister_all()
        self.tray.hide()
        self.s.save()
        self.app.quit()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Timetable")
    app.setApplicationVersion(__version__)
    app.setQuitOnLastWindowClosed(False)
    lock = QLockFile(QDir.temp().filePath("timetable.lock"))
    if not lock.tryLock(100):
        return 0  # already running
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("No system tray available; controls will not be reachable.", file=sys.stderr)
    ctl = Controller(app)  # noqa: F841 (kept alive by the event loop)
    return app.exec()
