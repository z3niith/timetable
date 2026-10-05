"""Headless check that the HUD paints in every mode without raising."""

import itertools
import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.parametrize("compact, click_through", list(itertools.product([False, True], repeat=2)))
def test_hud_paints(compact, click_through, tmp_path):
    from PySide6.QtWidgets import QApplication

    from timetable.agenda import parse_agenda
    from timetable.engine import TimerEngine
    from timetable.hud import Hud
    from timetable.sessions import SessionStore, parse_tasks
    from timetable.settings import DEFAULT_AGENDA, Settings

    app = QApplication.instance() or QApplication([])
    settings = Settings(compact=compact, click_through=click_through)
    store = SessionStore(tmp_path / "s.json")
    engine = TimerEngine(parse_agenda(DEFAULT_AGENDA))
    hud = Hud(engine, settings, store)

    def paint() -> None:
        app.processEvents()
        image = hud.grab().toImage()
        assert not image.isNull() and image.width() > 0

    paint()                                        # no tasks
    store.current.tasks = parse_tasks("Read chapter 3\nPractice problems")
    engine.start()
    engine.elapsed = 5
    paint()                                        # a current task
    store.current.tick_task()
    store.current.tick_task()
    paint()                                        # all tasks done
    store.current.name = "A very long session name " * 8
    store.current.tasks = parse_tasks("A very long task name " * 12)
    paint()                                        # long text must be cut, not crash
    engine.set_items([])
    paint()                                        # empty agenda
    hud.close()
