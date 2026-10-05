from timetable.agenda import Item
from timetable.history import HistoryLog
from timetable.sessions import SessionStore, format_tasks, parse_tasks


def test_parse_and_format_tasks():
    tasks = parse_tasks("[x] Read ch. 3\n[ ] Practice set\n- Flashcards\n\n# note\n* [X] Email TA")
    assert [(t.text, t.done) for t in tasks] == [
        ("Read ch. 3", True), ("Practice set", False), ("Flashcards", False), ("Email TA", True)
    ]
    assert format_tasks(tasks).splitlines()[0] == "[x] Read ch. 3"
    assert parse_tasks(format_tasks(tasks)) == tasks


def test_first_run_creates_a_session_from_legacy_agenda(tmp_path):
    store = SessionStore(tmp_path / "s.json", legacy_agenda="Study 50m")
    assert len(store.sessions) == 1
    assert store.current.agenda == "Study 50m"
    assert (tmp_path / "s.json").exists()


def test_everything_survives_a_reload(tmp_path):
    path = tmp_path / "s.json"
    store = SessionStore(path)
    chem = store.create("Chemistry", "Focus 25m", parse_tasks("[x] a\nb"))
    store.select(chem.id)
    again = SessionStore(path)
    assert again.current.name == "Chemistry"
    assert [(t.text, t.done) for t in again.current.tasks] == [("a", True), ("b", False)]


def test_names_stay_unique_and_last_session_is_protected(tmp_path):
    store = SessionStore(tmp_path / "s.json")
    a = store.create("Deep work")
    b = store.create("deep work")
    assert a.name != b.name
    copy = store.duplicate(a.id)
    assert copy.name == "Deep work copy" and all(not t.done for t in copy.tasks)
    store.rename(b.id, "Reading")
    assert store.get(b.id).name == "Reading"
    store.select(a.id)
    for s in list(store.sessions):
        store.delete(s.id)
    assert len(store.sessions) == 1  # the last one stays
    assert store.current_id == store.sessions[0].id


def test_tick_and_untick():
    from timetable.sessions import Session

    s = Session("x", "X", tasks=parse_tasks("a\nb"))
    assert s.current_task.text == "a"
    assert s.tick_task() and s.tick_task() and not s.tick_task()
    assert s.current_task is None
    assert s.untick_task() and s.current_task.text == "b"


def test_damaged_files_fall_back_safely(tmp_path):
    path = tmp_path / "s.json"
    path.write_text("{not json", encoding="utf-8")
    assert len(SessionStore(path).sessions) == 1


def test_history_log_appends_and_skips_damaged_lines(tmp_path):
    log = HistoryLog(tmp_path / "h.jsonl")
    log.add("id1", "Chemistry", Item("Focus", 1500), "completed", 1500)
    log.add("id1", "Chemistry", Item("Break", 300), "skipped", 42.4)
    with log.path.open("a", encoding="utf-8") as f:
        f.write("garbage\n")
    records = log.read()
    assert [r["event"] for r in records] == ["completed", "skipped"]
    assert records[1]["is_break"] is True and records[1]["spent_seconds"] == 42
