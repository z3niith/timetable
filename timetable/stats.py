"""Turns history.jsonl records into the numbers the Stats window draws. No GUI code here.

Only focus time counts (breaks and sub-second intervals are ignored). An entry that crosses
midnight is split, so every day's total and timeline add up on their own.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

OTHER = "Other"
OTHER_COLOR = "#7f8a9b"
MAX_SLICES = 8  # one per palette colour; the rest fold into "Other"


@dataclass(frozen=True)
class Entry:
    start: datetime  # local, naive
    end: datetime
    session_id: str
    session: str
    color: str
    task: str

    @property
    def seconds(self) -> float:
        return (self.end - self.start).total_seconds()

    @property
    def day(self) -> date:
        return self.start.date()


@dataclass(frozen=True)
class Slice:
    name: str
    color: str
    seconds: float


def _parse_time(text: str) -> datetime | None:
    try:
        t = datetime.fromisoformat(text)
    except (TypeError, ValueError):
        return None
    return t.astimezone().replace(tzinfo=None) if t.tzinfo else t


def load_entries(records: list[dict]) -> list[Entry]:
    entries: list[Entry] = []
    for r in records:
        try:
            spent = float(r.get("spent_seconds", 0))
        except (TypeError, ValueError):
            continue
        end = _parse_time(r.get("time", ""))
        if r.get("is_break") or spent < 1 or end is None:
            continue
        start = end - timedelta(seconds=spent)
        base = dict(
            session_id=str(r.get("session_id", "")),
            session=str(r.get("session", "Session")),
            color=str(r.get("color") or ""),
            task=str(r.get("task") or ""),
        )
        while start.date() != end.date():  # split at midnight
            midnight = datetime.combine(start.date() + timedelta(days=1), datetime.min.time())
            entries.append(Entry(start, midnight, **base))
            start = midnight
        entries.append(Entry(start, end, **base))
    entries.sort(key=lambda e: e.start)
    return entries


def week_start(day: date) -> date:
    """Weeks run Sunday to Saturday."""
    return day - timedelta(days=(day.weekday() + 1) % 7)


def month_range(day: date) -> tuple[date, date]:
    first = day.replace(day=1)
    nxt = (first + timedelta(days=32)).replace(day=1)
    return first, nxt - timedelta(days=1)


def _within(entries: list[Entry], first: date, last: date) -> list[Entry]:
    return [e for e in entries if first <= e.day <= last]


def day_totals(entries: list[Entry], first: date, last: date) -> dict[date, float]:
    totals: dict[date, float] = defaultdict(float)
    for e in _within(entries, first, last):
        totals[e.day] += e.seconds
    return dict(totals)


def breakdown(entries: list[Entry], first: date, last: date) -> list[Slice]:
    """Time per session, largest first; beyond MAX_SLICES the rest become one 'Other' slice."""
    sums: dict[str, float] = defaultdict(float)
    colors: dict[str, str] = {}
    for e in _within(entries, first, last):
        sums[e.session] += e.seconds
        colors[e.session] = e.color or colors.get(e.session, "")
    ranked = sorted(sums.items(), key=lambda kv: -kv[1])
    slices = [Slice(n, colors[n] or OTHER_COLOR, s) for n, s in ranked]
    if len(slices) > MAX_SLICES:
        rest = sum(s.seconds for s in slices[MAX_SLICES - 1:])
        slices = slices[: MAX_SLICES - 1] + [Slice(OTHER, OTHER_COLOR, rest)]
    return slices


def daily_stacks(entries: list[Entry], first: date, last: date) -> dict[date, list[Slice]]:
    """Per-day time by session (sessions in a fixed, alphabetical order so colours stay put)."""
    per: dict[date, dict[str, list]] = defaultdict(dict)
    for e in _within(entries, first, last):
        slot = per[e.day].setdefault(e.session, [0.0, e.color or OTHER_COLOR])
        slot[0] += e.seconds
    return {d: [Slice(n, v[1], v[0]) for n, v in sorted(m.items())] for d, m in per.items()}


def segments(entries: list[Entry], day: date) -> list[tuple[float, float, Slice]]:
    """(start second of day, end second of day, session) for the hourly strip."""
    out = []
    for e in entries:
        if e.day == day:
            s = (e.start - datetime.combine(day, datetime.min.time())).total_seconds()
            out.append((s, s + e.seconds, Slice(e.session, e.color or OTHER_COLOR, e.seconds)))
    return out


def top_tasks(entries: list[Entry], first: date, last: date, limit: int = 5) -> list[tuple[str, float]]:
    sums: dict[str, float] = defaultdict(float)
    for e in _within(entries, first, last):
        if e.task:
            sums[e.task] += e.seconds
    return sorted(sums.items(), key=lambda kv: -kv[1])[:limit]


def totals(entries: list[Entry], today: date) -> dict[str, float]:
    wk = week_start(today)
    m_first, m_last = month_range(today)
    return {
        "today": sum(e.seconds for e in _within(entries, today, today)),
        "week": sum(e.seconds for e in _within(entries, wk, wk + timedelta(days=6))),
        "month": sum(e.seconds for e in _within(entries, m_first, m_last)),
        "all": sum(e.seconds for e in entries),
    }


def streak(entries: list[Entry], today: date) -> int:
    """Consecutive days with focus time, counting back from today (or yesterday if today is still empty)."""
    days = {e.day for e in entries}
    cursor = today if today in days else today - timedelta(days=1)
    n = 0
    while cursor in days:
        n += 1
        cursor -= timedelta(days=1)
    return n


def fmt_duration(seconds: float) -> str:
    minutes = int(round(seconds / 60))
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"
