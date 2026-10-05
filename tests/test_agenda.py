from timetable.agenda import format_clock, format_short, parse_agenda, parse_duration


def test_durations():
    assert parse_duration("50m") == 3000
    assert parse_duration("1h30m") == 5400
    assert parse_duration("1h 30m") == 5400
    assert parse_duration("45s") == 45
    assert parse_duration("10") == 600


def test_original_agenda_format():
    items = parse_agenda("Welcome & context 5m\n60 60m\nBreak 10m\n10 10m\n")
    assert [(i.name, i.seconds) for i in items] == [
        ("Welcome & context", 300), ("60", 3600), ("Break", 600), ("10", 600)
    ]
    assert items[2].is_break and not items[1].is_break


def test_skips_junk_and_comments():
    items = parse_agenda("# plan\n\nLunch\nRead 20min\nBare 15\n")
    assert [(i.name, i.seconds) for i in items] == [("Read", 1200), ("Bare", 900)]


def test_formatting():
    assert format_clock(300) == "05:00"
    assert format_clock(3725) == "1:02:05"
    assert format_short(3600) == "1h" and format_short(5400) == "1h30m" and format_short(300) == "5m"
