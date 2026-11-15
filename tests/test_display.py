"""Always-on-top and monitor handling."""

import os
from types import SimpleNamespace

import pytest

from timetable import winpos
from timetable.screens import Rect, dock_rect, pick_screen, screen_key


class FakeUser32:
    def __init__(self, style=0):
        self.calls, self.style = [], style

    def SetWindowPos(self, *args):  # noqa: N802
        self.calls.append(("pos", args))
        return 1

    def GetWindowLongW(self, hwnd, index):  # noqa: N802
        return self.style

    def SetWindowLongW(self, hwnd, index, value):  # noqa: N802
        self.calls.append(("style", value))
        self.style = value


def test_raise_topmost_does_not_activate_or_move():
    u = FakeUser32()
    assert winpos.raise_topmost(42, u)
    _, (hwnd, after, x, y, w, h, flags) = u.calls[0]
    assert (hwnd, after) == (42, winpos.HWND_TOPMOST)
    assert flags & winpos.SWP_NOACTIVATE and flags & winpos.SWP_NOMOVE and flags & winpos.SWP_NOSIZE


def test_no_activate_style_is_only_written_once():
    u = FakeUser32()
    winpos.mark_no_activate(1, u)
    winpos.mark_no_activate(1, u)
    assert [c[0] for c in u.calls] == ["style"]
    assert u.style & winpos.WS_EX_NOACTIVATE


def screen(name, serial=""):
    return SimpleNamespace(name=lambda: name, serialNumber=lambda: serial)


def test_picks_chosen_monitor_else_primary():
    laptop, external = screen(r"\\.\DISPLAY1", "A"), screen(r"\\.\DISPLAY2", "B")
    both = [laptop, external]
    assert pick_screen(both, laptop, screen_key(external)) is external
    assert pick_screen(both, laptop, "") is laptop
    # the chosen monitor was unplugged: fall back to what is left
    assert pick_screen([laptop], laptop, screen_key(external)) is laptop


def test_dock_rect_for_a_new_resolution():
    assert dock_rect(Rect(0, 0, 1920, 1080), 86, "top", 0) == Rect(0, 0, 1920, 86)
    # unplugging the external monitor: the 1920x1200 laptop screen gets a full-width bar
    assert dock_rect(Rect(0, 0, 1920, 1200), 86, "top", 0) == Rect(0, 0, 1920, 86)
    assert dock_rect(Rect(0, 0, 1920, 1160), 46, "bottom", 8) == Rect(0, 1106, 1920, 46)
    assert dock_rect(Rect(0, 0, 100, 40), 86, "top", 0).h == 40  # never taller than the screen


@pytest.fixture
def hud(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from timetable.agenda import parse_agenda
    from timetable.engine import TimerEngine
    from timetable.hud import Hud
    from timetable.sessions import SessionStore
    from timetable.settings import DEFAULT_AGENDA, Settings

    app = QApplication.instance() or QApplication([])
    h = Hud(TimerEngine(parse_agenda(DEFAULT_AGENDA)), Settings(), SessionStore(tmp_path / "s.json"))
    yield app, h
    h.close()


def test_hud_resizes_when_the_screen_changes(hud):
    from PySide6.QtTest import QTest

    app, h = hud
    area = {"rect": Rect(0, 0, 1920, 1080)}
    h.target_rect = lambda: dock_rect(area["rect"], 86, "top", 0)
    h.reposition()
    assert h.width() == 1920

    area["rect"] = Rect(0, 0, 2560, 1440)      # resolution changes / other monitor becomes the target
    app.primaryScreenChanged.emit(app.primaryScreen())
    QTest.qWait(600)                           # wait for the settle timer
    assert (h.width(), h.x()) == (2560, 0)


def test_hud_keeps_asserting_top(hud, monkeypatch):
    import timetable.hud as hud_module

    app, h = hud
    seen = []
    monkeypatch.setattr(hud_module, "raise_topmost", lambda hwnd: seen.append(hwnd))
    h.s.keep_on_top = True
    h._assert_top()
    assert len(seen) == 1
    h.s.keep_on_top = False
    h._assert_top()
    assert len(seen) == 1
