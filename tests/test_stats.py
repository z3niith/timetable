from datetime import date

from timetable import stats


def rec(time, spent, session="Study", color="#3987e5", is_break=False, task=""):
    return {"time": time, "spent_seconds": spent, "session": session, "session_id": session,
            "color": color, "is_break": is_break, "task": task}


def entries(*records):
    return stats.load_entries(list(records))


def test_breaks_and_tiny_intervals_are_ignored():
    e = entries(rec("2026-11-10T10:00:00", 600), rec("2026-11-10T10:10:00", 300, is_break=True),
                rec("2026-11-10T10:11:00", 0), {"time": "garbage", "spent_seconds": 5})
    assert len(e) == 1 and e[0].seconds == 600


def test_midnight_split():
    e = entries(rec("2026-11-11T00:10:00", 1800))
    assert [x.day for x in e] == [date(2026, 11, 10), date(2026, 11, 11)]
    assert [x.seconds for x in e] == [1200, 600]


def test_week_starts_sunday_and_month_range():
    assert stats.week_start(date(2026, 11, 15)) == date(2026, 11, 15)  # a Sunday
    assert stats.week_start(date(2026, 11, 14)) == date(2026, 11, 8)
    assert stats.month_range(date(2026, 2, 9)) == (date(2026, 2, 1), date(2026, 2, 28))


def test_breakdown_folds_into_other():
    recs = [rec(f"2026-11-10T1{i}:00:00", 600 + i * 60, session=f"S{i}") for i in range(9)]
    out = stats.breakdown(entries(*recs), date(2026, 11, 10), date(2026, 11, 10))
    assert len(out) == stats.MAX_SLICES and out[-1].name == stats.OTHER
    assert out[0].name == "S8" and abs(sum(s.seconds for s in out) - sum(600 + i * 60 for i in range(9))) < 1


def test_segments_top_tasks_totals_streak():
    e = entries(rec("2026-11-14T09:30:00", 1800, task="Essay"), rec("2026-11-15T10:00:00", 1500, task="Essay"),
                rec("2026-11-15T11:00:00", 600, task="Lab"))
    start, end, s = stats.segments(e, date(2026, 11, 15))[0]
    assert (start, end) == (9 * 3600 + 35 * 60, 10 * 3600) and s.name == "Study"
    assert stats.top_tasks(e, date(2026, 11, 1), date(2026, 11, 30))[0] == ("Essay", 3300)
    t = stats.totals(e, date(2026, 11, 15))
    assert t["today"] == 2100 and t["week"] == 2100 and t["month"] == 3900 and t["all"] == 3900
    assert stats.streak(e, date(2026, 11, 15)) == 2
    assert stats.streak(e, date(2026, 11, 17)) == 0
    assert stats.fmt_duration(3900) == "1h 05m"
