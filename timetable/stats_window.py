"""The Stats window: Day, Week and Month views of your focus time."""

from __future__ import annotations

from datetime import date, timedelta

from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from . import stats
from .charts import DayStrip, Donut, MonthCalendar, RankedBars, StackedBars, StatCard
from .history import HistoryLog

MODES = ("Day", "Week", "Month")


class StatsWindow(QDialog):
    def __init__(self, history: HistoryLog, accent: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.history, self.accent = history, accent
        self.setWindowTitle("Timetable stats")
        self.resize(900, 780)
        self.mode = "Day"
        self.day = date.today()

        # header: segmented Day/Week/Month + date navigator
        self.mode_buttons: dict[str, QPushButton] = {}
        group = QButtonGroup(self)
        header = QHBoxLayout()
        for name in MODES:
            b = QPushButton(name)
            b.setCheckable(True)
            b.setChecked(name == self.mode)
            group.addButton(b)
            b.clicked.connect(lambda _=False, n=name: self.set_mode(n))
            self.mode_buttons[name] = b
            header.addWidget(b)
        header.addStretch(1)
        prev_b, next_b, today_b = QPushButton("<"), QPushButton(">"), QPushButton("Today")
        self.range_label = QLabel()
        self.range_label.setMinimumWidth(190)
        self.range_label.setStyleSheet("font-size: 15px; font-weight: 600;")
        for b in (prev_b, next_b):
            b.setFixedWidth(36)
        prev_b.clicked.connect(lambda: self.step(-1))
        next_b.clicked.connect(lambda: self.step(1))
        today_b.clicked.connect(self.go_today)
        for w in (prev_b, self.range_label, next_b, today_b):
            header.addWidget(w)

        # content
        self.cards = {k: StatCard(label) for k, label in (
            ("today", "Today"), ("week", "This week"), ("month", "This month"), ("streak", "Day streak"))}
        cards_row = QHBoxLayout()
        for c in self.cards.values():
            cards_row.addWidget(c)

        self.calendar = MonthCalendar(accent)
        self.donut = Donut()
        self.strip = DayStrip()
        self.bars = StackedBars()
        self.tasks = RankedBars("Top tasks", accent)
        self.calendar.day_clicked.connect(self.pick_day)

        self.grid = grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(self.calendar, 0, 0)
        grid.addWidget(self.donut, 0, 1)
        grid.addWidget(self.strip, 1, 0, 1, 2)
        grid.addWidget(self.bars, 2, 0, 1, 2)
        grid.addWidget(self.tasks, 3, 0, 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        inner = QWidget()
        col = QVBoxLayout(inner)
        col.setSpacing(12)
        col.addLayout(cards_row)
        col.addLayout(grid)
        col.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(inner)

        lay = QVBoxLayout(self)
        lay.addLayout(header)
        lay.addWidget(scroll)
        self.refresh()

    # -- navigation --------------------------------------------------------
    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.refresh()

    def step(self, direction: int) -> None:
        if self.mode == "Day":
            self.day += timedelta(days=direction)
        elif self.mode == "Week":
            self.day += timedelta(days=7 * direction)
        else:
            first = self.day.replace(day=1)
            self.day = (first + timedelta(days=32 if direction > 0 else -1)).replace(day=1)
        self.refresh()

    def go_today(self) -> None:
        self.day = date.today()
        self.refresh()

    def pick_day(self, d: date) -> None:
        self.day = d
        if self.mode == "Month":
            self.mode_buttons["Day"].setChecked(True)
            self.mode = "Day"
        self.refresh()

    def set_accent(self, accent: str) -> None:
        self.accent = accent
        self.refresh()

    def _range(self) -> tuple[date, date]:
        if self.mode == "Day":
            return self.day, self.day
        if self.mode == "Week":
            first = stats.week_start(self.day)
            return first, first + timedelta(days=6)
        return stats.month_range(self.day)

    # -- drawing -----------------------------------------------------------
    def refresh(self) -> None:
        entries = stats.load_entries(self.history.read())
        first, last = self._range()
        today = date.today()
        self.range_label.setText(self._title(first, last))

        t = stats.totals(entries, today)
        self.cards["today"].set_value(stats.fmt_duration(t["today"]))
        self.cards["week"].set_value(stats.fmt_duration(t["week"]))
        self.cards["month"].set_value(stats.fmt_duration(t["month"]))
        n = stats.streak(entries, today)
        self.cards["streak"].set_value(f"{n} day{'s' if n != 1 else ''}")

        m_first, m_last = stats.month_range(self.day)
        self.calendar.set_data(m_first, stats.day_totals(entries, m_first, m_last), self.day, self.accent)
        self.donut.set_data(stats.breakdown(entries, first, last))
        self.strip.set_data(stats.segments(entries, self.day))
        days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
        self.bars.set_data(days, stats.daily_stacks(entries, first, last), 1 if len(days) <= 7 else 3)
        self.tasks.set_data(stats.top_tasks(entries, first, last), self.accent)

        show = {"Day": (True, True, True, False), "Week": (False, True, False, True), "Month": (True, True, False, True)}
        cal, donut, strip, bars = show[self.mode]
        self.grid.addWidget(self.donut, 0, 1 if cal else 0, 1, 1 if cal else 2)  # fill the row when no calendar
        self.calendar.setVisible(cal)
        self.donut.setVisible(donut)
        self.strip.setVisible(strip)
        self.bars.setVisible(bars)
        self.bars.title = "Focus time per day"

    def _title(self, first: date, last: date) -> str:
        if self.mode == "Day":
            return f"{first:%a, %b} {first.day}, {first.year}"
        if self.mode == "Week":
            return f"{first:%b} {first.day} - {last:%b} {last.day}, {last.year}"
        return f"{first:%B %Y}"

    def showEvent(self, ev) -> None:  # noqa: N802
        self.refresh()
        super().showEvent(ev)
