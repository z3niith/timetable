"""Headless tests of the app wiring: sessions, tasks and history logging."""

import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def ctl(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    from PySide6.QtWidgets import QApplication

    from timetable.app import Controller

    app = QApplication.instance() or QApplication([])
    c = Controller(app)
    yield c
    c.hud.close()


def answer(monkeypatch, button):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", staticmethod(lambda *a, **k: button))


def test_switching_sessions_loads_its_agenda(ctl):
    chem = ctl.store.create("Chemistry", "Focus 40m\nBreak 5m")
    ctl.switch_session(chem.id)
    assert ctl.store.current.name == "Chemistry"
    assert [i.name for i in ctl.engine.items] == ["Focus", "Break"]


def test_switch_asks_before_discarding_progress(ctl, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    other = ctl.store.create("Other", "Read 10m")
    ctl.do("toggle")
    ctl.engine.elapsed = 30

    answer(monkeypatch, QMessageBox.No)
    ctl.switch_session(other.id)
    assert ctl.store.current_id != other.id and ctl.engine.elapsed == 30

    answer(monkeypatch, QMessageBox.Yes)
    ctl.switch_session(other.id)
    assert ctl.store.current_id == other.id and ctl.engine.elapsed == 0


def test_task_hotkey_actions(ctl):
    from timetable.sessions import parse_tasks

    ctl._tasks_edited("First\nSecond")
    assert [t.text for t in ctl.store.current.tasks] == ["First", "Second"]
    ctl.do("task")
    assert ctl.store.current.tasks[0].done and ctl.store.current.current_task.text == "Second"
    ctl.do("untask")
    assert not ctl.store.current.tasks[0].done
    assert parse_tasks("x")[0].text == "x"


def test_history_records_completed_and_skipped(ctl):
    ctl._agenda_edited("A 1m\nB 1m\nC 1m")
    ctl.do("toggle")
    ctl.engine.elapsed = 61          # first interval runs out
    ctl.engine.tick()
    ctl.engine.elapsed = 20
    ctl.do("skip")                   # second interval is skipped after 20 s
    events = [(r["interval"], r["event"], r["spent_seconds"]) for r in ctl.history.read()]
    assert events[0] == ("A", "completed", 60)
    assert events[1][:2] == ("B", "skipped") and 19 <= events[1][2] <= 21


def test_editing_the_agenda_updates_the_running_timer(ctl):
    ctl._agenda_edited("Only 5m")
    assert [i.name for i in ctl.engine.items] == ["Only"]
    assert ctl.store.current.agenda == "Only 5m"


def test_partial_interval_is_logged_with_task_and_color(ctl):
    ctl.store.current.tasks = [__import__("timetable.sessions", fromlist=["Task"]).Task("Read ch. 3")]
    ctl.do("toggle")
    ctl.engine.elapsed = 90
    ctl.do("restart")
    rec = ctl.history.read()[-1]
    assert rec["event"] == "stopped" and rec["spent_seconds"] == 90
    assert rec["task"] == "Read ch. 3" and rec["color"] == ctl.store.current.color


def test_nothing_logged_when_idle(ctl):
    ctl.do("restart")
    assert ctl.history.read() == []


def test_new_sessions_get_distinct_colors(ctl):
    a = ctl.store.create("A")
    b = ctl.store.create("B")
    assert len({ctl.store.sessions[0].color, a.color, b.color}) == 3
