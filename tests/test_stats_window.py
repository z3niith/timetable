"""Smoke tests: the Stats window and charts draw with real and empty data."""

import json
import os
from datetime import datetime

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def window(tmp_path):
    from PySide6.QtWidgets import QApplication

    from timetable.history import HistoryLog
    from timetable.stats_window import StatsWindow

    QApplication.instance() or QApplication([])
    log = HistoryLog(tmp_path / "history.jsonl")
    w = StatsWindow(log, "#2dd4bf")
    yield w, log
    w.close()


def test_empty_history_draws_every_mode(window):
    w, _ = window
    for mode in ("Day", "Week", "Month"):
        w.set_mode(mode)
        assert w.grab().width() > 0
    assert w.cards["streak"].value == "0 days"


def test_entries_show_in_cards_and_navigation_works(window):
    w, log = window
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    log.path.write_text(json.dumps({"time": now, "session_id": "a", "session": "Study", "color": "#3987e5",
                                    "is_break": False, "spent_seconds": 1500, "task": "Essay"}) + "\n")
    w.refresh()
    assert w.cards["today"].value == "25m"
    w.set_mode("Week")
    w.step(-1)
    w.step(1)
    w.set_mode("Month")
    w.step(1)
    w.go_today()
    assert w.tasks.rows == [("Essay", 1500)]


def test_clicking_a_calendar_day_opens_that_day(window):
    from datetime import date

    w, _ = window
    w.set_mode("Month")
    target = date.today().replace(day=1)
    w.calendar.day_clicked.emit(target)
    assert w.mode == "Day" and w.day == target
