from timetable.agenda import Item
from timetable.engine import State, TimerEngine


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def make(items):
    clock = FakeClock()
    eng = TimerEngine(items, clock)
    events = []
    eng.on_interval_end = lambda item, last: events.append((item.name, last))
    return eng, clock, events


def test_runs_through_and_dings_each_interval():
    eng, clock, events = make([Item("A", 10), Item("Break", 5), Item("B", 10)])
    eng.start()
    clock.t = 10.5
    eng.tick()
    assert eng.index == 1 and events == [("A", False)]
    clock.t = 15.5
    eng.tick()
    assert eng.index == 2
    clock.t = 40
    eng.tick()
    assert eng.state is State.FINISHED
    assert events == [("A", False), ("Break", False), ("B", True)]


def test_pause_does_not_advance():
    eng, clock, _ = make([Item("A", 10)])
    eng.start()
    clock.t = 4
    eng.pause()
    clock.t = 100
    eng.tick()
    assert round(eng.elapsed) == 4 and eng.state is State.PAUSED


def test_skip_is_silent_and_adjust_clamps():
    eng, clock, events = make([Item("A", 100), Item("B", 100)])
    eng.start()
    eng.adjust(-1000)
    assert eng.current.seconds == 1
    eng.skip()
    assert eng.index == 1 and events == []


def test_live_agenda_edit_keeps_position():
    eng, clock, _ = make([Item("A", 100), Item("B", 100)])
    eng.start()
    clock.t = 30
    eng.tick()
    eng.set_items([Item("A", 200), Item("B", 100), Item("C", 50)])
    assert eng.index == 0 and round(eng.elapsed) == 30
