"""Small custom-painted charts for the Stats window. Native QPainter, no extra libraries.

Every chart keeps a list of hit boxes so hovering shows the exact value, and none of them
relies on colour alone: legends and labels carry the names.
"""

from __future__ import annotations

import calendar
from datetime import date

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QToolTip, QWidget

from . import theme
from .stats import Slice, fmt_duration

SURFACE, BORDER = QColor(theme.SURFACE), QColor(theme.BORDER)
TEXT, DIM, FAINT = QColor(theme.TEXT), QColor(theme.DIM), QColor(theme.FAINT)
GAP = 2.0  # surface-coloured gap between touching fills


def _font(size: float, bold: bool = False) -> QFont:
    f = QFont("Segoe UI")
    f.setPixelSize(int(size))
    f.setBold(bold)
    return f


class Chart(QWidget):
    """Base: a rounded card, hover hit boxes, and an optional title."""

    def __init__(self, title: str = "", min_h: int = 160, parent: QWidget | None = None):
        super().__init__(parent)
        self.title = title
        self.setMinimumHeight(min_h)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._hits: list[tuple[QRectF, str]] = []

    def begin(self) -> tuple[QPainter, QRectF]:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self._hits = []
        card = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(BORDER, 1))
        p.setBrush(SURFACE)
        p.drawRoundedRect(card, 12, 12)
        body = card.adjusted(16, 14, -16, -14)
        if self.title:
            p.setFont(_font(12, True))
            p.setPen(DIM)
            p.drawText(QRectF(body.left(), body.top(), body.width(), 18), Qt.AlignLeft | Qt.AlignVCenter, self.title)
            body.setTop(body.top() + 26)
        return p, body

    def text(self, p, s, rect, size=12, colour=DIM, align=Qt.AlignLeft | Qt.AlignVCenter, bold=False) -> None:
        p.setFont(_font(size, bold))
        p.setPen(colour)
        p.drawText(rect, align, s)

    def empty(self, p, body, message="No focus time recorded yet") -> None:
        self.text(p, message, body, 13, FAINT, Qt.AlignCenter)

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802
        pos = ev.position()
        for rect, tip in self._hits:
            if rect.contains(pos):
                QToolTip.showText(ev.globalPosition().toPoint(), tip, self)
                return
        QToolTip.hideText()


class StatCard(Chart):
    """One headline number with a label under it."""

    def __init__(self, label: str, parent: QWidget | None = None):
        super().__init__("", 78, parent)
        self.label, self.value = label, "0m"
        self.setMaximumHeight(86)

    def set_value(self, value: str) -> None:
        self.value = value
        self.update()

    def paintEvent(self, _ev) -> None:  # noqa: N802
        p, body = self.begin()
        self.text(p, self.value, QRectF(body.left(), body.top(), body.width(), 30), 22, TEXT, bold=True)
        self.text(p, self.label, QRectF(body.left(), body.top() + 32, body.width(), 16), 11, DIM)
        p.end()


class MonthCalendar(Chart):
    """Month grid; each day is shaded by focus time. Click a day to select it."""

    day_clicked = Signal(object)

    def __init__(self, accent: str = "#2dd4bf", parent: QWidget | None = None):
        super().__init__("", 250, parent)
        self.accent = QColor(accent)
        self.month = date.today().replace(day=1)
        self.totals: dict[date, float] = {}
        self.selected: date | None = None

    def set_data(self, month: date, totals: dict[date, float], selected: date | None, accent: str) -> None:
        self.month, self.totals, self.selected, self.accent = month.replace(day=1), totals, selected, QColor(accent)
        self.update()

    def _cells(self, body: QRectF):
        weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(self.month.year, self.month.month)
        top = body.top() + 22
        cw, ch = body.width() / 7, (body.bottom() - top) / len(weeks)
        for r, week in enumerate(weeks):
            for c, d in enumerate(week):
                yield d, QRectF(body.left() + c * cw, top + r * ch, cw, ch).adjusted(GAP, GAP, -GAP, -GAP)

    def paintEvent(self, _ev) -> None:  # noqa: N802
        p, body = self.begin()
        cw = body.width() / 7
        for i, name in enumerate(("S", "M", "T", "W", "T", "F", "S")):
            self.text(p, name, QRectF(body.left() + i * cw, body.top(), cw, 18), 11, FAINT, Qt.AlignCenter)
        peak = max(self.totals.values(), default=0)
        today = date.today()
        for d, rect in self._cells(body):
            inside = d.month == self.month.month
            secs = self.totals.get(d, 0) if inside else 0
            fill = QColor(self.accent)
            fill.setAlphaF(0.16 + 0.74 * (secs / peak) if secs and peak else 0)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.RAISED) if inside else Qt.NoBrush)
            p.drawRoundedRect(rect, 6, 6)
            if secs:
                p.setBrush(fill)
                p.drawRoundedRect(rect, 6, 6)
            if d == self.selected:
                p.setPen(QPen(TEXT, 1.6))
                p.setBrush(Qt.NoBrush)
                p.drawRoundedRect(rect, 6, 6)
            strong = secs and secs > peak * 0.55
            colour = QColor("#04121a") if strong else (TEXT if inside else FAINT)
            self.text(p, str(d.day), rect, 12, colour, Qt.AlignCenter, bold=d == today)
            if d == today:
                p.setPen(Qt.NoPen)
                p.setBrush(colour)
                p.drawEllipse(QPointF(rect.center().x(), rect.bottom() - 5), 1.8, 1.8)
            if inside:
                tip = f"{d:%a %b} {d.day}: " + (fmt_duration(secs) if secs else "no focus time")
                self._hits.append((rect, tip))
        p.end()

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        body = QRectF(self.rect()).adjusted(16.5, 14.5, -16.5, -14.5)
        for d, rect in self._cells(body):
            if rect.contains(ev.position()) and d.month == self.month.month:
                self.day_clicked.emit(d)
                return


class Donut(Chart):
    """Share of time per session, total in the middle, legend on the right."""

    def __init__(self, title: str = "By session", parent: QWidget | None = None):
        super().__init__(title, 210, parent)
        self.slices: list[Slice] = []

    def set_data(self, slices: list[Slice]) -> None:
        self.slices = [s for s in slices if s.seconds > 0]
        self.update()

    def paintEvent(self, _ev) -> None:  # noqa: N802
        p, body = self.begin()
        total = sum(s.seconds for s in self.slices)
        if not total:
            self.empty(p, body)
            p.end()
            return
        size = min(body.height(), body.width() * 0.5)
        ring = QRectF(body.left() + 8, body.center().y() - size / 2 + 8, size - 16, size - 16)
        width = size * 0.17
        arc = ring.adjusted(width / 2, width / 2, -width / 2, -width / 2)
        start = 90.0
        gap_deg = 2.5 if len(self.slices) > 1 else 0
        for s in self.slices:
            span = 360 * s.seconds / total
            pen = QPen(QColor(s.color), width, Qt.SolidLine, Qt.FlatCap)
            p.setPen(pen)
            p.drawArc(arc, int((start - gap_deg / 2) * 16), int(-max(span - gap_deg, 0.5) * 16))
            start -= span
        self.text(p, fmt_duration(total), QRectF(ring.left(), ring.center().y() - 16, ring.width(), 26), 20, TEXT, Qt.AlignCenter, True)
        self.text(p, "focused", QRectF(ring.left(), ring.center().y() + 8, ring.width(), 16), 11, DIM, Qt.AlignCenter)
        # legend
        x, row_h = ring.right() + 28, 24
        y = body.center().y() - row_h * len(self.slices) / 2
        for s in self.slices:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(s.color))
            p.drawRoundedRect(QRectF(x, y + 7, 10, 10), 3, 3)
            name = QFontMetrics(_font(12)).elidedText(s.name, Qt.ElideRight, int(body.right() - x - 110))
            self.text(p, name, QRectF(x + 18, y, body.right() - x - 18, row_h), 12, TEXT)
            self.text(p, f"{fmt_duration(s.seconds)}  {s.seconds / total:.0%}", QRectF(x, y, body.right() - x, row_h), 12, DIM, Qt.AlignRight | Qt.AlignVCenter)
            self._hits.append((QRectF(x, y, body.right() - x, row_h), f"{s.name}: {fmt_duration(s.seconds)} ({s.seconds / total:.0%})"))
            y += row_h
        p.end()


class DayStrip(Chart):
    """The day as a 24-hour strip; coloured blocks show when you focused."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Timeline", 110, parent)
        self.segs: list[tuple[float, float, Slice]] = []

    def set_data(self, segs) -> None:
        self.segs = segs
        self.update()

    def paintEvent(self, _ev) -> None:  # noqa: N802
        p, body = self.begin()
        bar = QRectF(body.left(), body.top() + 4, body.width(), body.height() - 26)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.RAISED))
        p.drawRoundedRect(bar, 6, 6)
        p.setPen(QPen(BORDER, 1))
        for h in range(0, 25, 3):
            x = bar.left() + bar.width() * h / 24
            p.drawLine(QPointF(x, bar.bottom() + 2), QPointF(x, bar.bottom() + 6))
            self.text(p, f"{h:02d}", QRectF(x - 14, bar.bottom() + 6, 28, 14), 10, FAINT, Qt.AlignCenter)
        for start, end, s in self.segs:
            r = QRectF(bar.left() + bar.width() * start / 86400, bar.top(), max(2.0, bar.width() * (end - start) / 86400), bar.height())
            p.setPen(QPen(QColor(theme.RAISED), GAP))  # surface-coloured edge keeps neighbours apart
            p.setBrush(QColor(s.color))
            p.drawRoundedRect(r, 3, 3)
            h0, m0 = divmod(int(start // 60), 60)
            h1, m1 = divmod(int(end // 60), 60)
            self._hits.append((r.adjusted(-2, 0, 2, 0), f"{s.name} {h0:02d}:{m0:02d}-{h1:02d}:{m1:02d} ({fmt_duration(end - start)})"))
        if not self.segs:
            self.text(p, "Nothing recorded this day", bar, 12, FAINT, Qt.AlignCenter)
        p.end()


class StackedBars(Chart):
    """One bar per day, stacked by session. Axis in hours."""

    def __init__(self, title: str = "Focus time per day", parent: QWidget | None = None):
        super().__init__(title, 210, parent)
        self.days: list[date] = []
        self.stacks: dict[date, list[Slice]] = {}
        self.label_every = 1

    def set_data(self, days: list[date], stacks: dict[date, list[Slice]], label_every: int = 1) -> None:
        self.days, self.stacks, self.label_every = days, stacks, label_every
        self.update()

    @staticmethod
    def _nice_step(seconds: float) -> float:
        """Gridline spacing (four gridlines) that lands on round times."""
        for step in (300, 600, 900, 1800, 3600, 7200, 10800, 14400):
            if seconds <= step * 4:
                return step
        return 14400

    def paintEvent(self, _ev) -> None:  # noqa: N802
        p, body = self.begin()
        peak = max((sum(s.seconds for s in v) for v in self.stacks.values()), default=0)
        if not peak:
            self.empty(p, body)
            p.end()
            return
        step = self._nice_step(peak)
        top = step * 4
        plot = QRectF(body.left() + 48, body.top() + 6, body.width() - 48, body.height() - 30)
        for i in range(5):
            y = plot.bottom() - plot.height() * i / 4
            p.setPen(QPen(BORDER, 1))
            p.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            self.text(p, "0" if i == 0 else fmt_duration(step * i), QRectF(body.left(), y - 8, 42, 16), 10, FAINT, Qt.AlignRight | Qt.AlignVCenter)
        n = len(self.days)
        slot = plot.width() / n
        bw = min(34.0, slot * 0.62)
        for i, d in enumerate(self.days):
            cx = plot.left() + slot * (i + 0.5)
            y = plot.bottom()
            slices = self.stacks.get(d, [])
            for k, s in enumerate(slices):
                h = plot.height() * s.seconds / top
                seg = QRectF(cx - bw / 2, y - h, bw, h)
                draw = seg.adjusted(0, GAP / 2 if k else 0, 0, -GAP / 2 if k < len(slices) - 1 else 0)
                path = QPainterPath()
                radius = 4 if k == len(slices) - 1 else 0.5  # rounded data-end only
                path.addRoundedRect(draw, radius, radius)
                p.setPen(Qt.NoPen)
                p.setBrush(QColor(s.color))
                p.drawPath(path)
                y -= h
            total = sum(s.seconds for s in slices)
            tip = f"{d:%a %b} {d.day}: {fmt_duration(total)}" if total else f"{d:%a %b} {d.day}: no focus time"
            tip += "".join(f"\n{s.name}: {fmt_duration(s.seconds)}" for s in slices)
            self._hits.append((QRectF(cx - slot / 2, plot.top(), slot, plot.height()), tip))
            if i % self.label_every == 0:
                label = f"{d:%a}"[0:3] if n <= 7 else str(d.day)
                self.text(p, label, QRectF(cx - slot, plot.bottom() + 4, slot * 2, 16), 10, DIM, Qt.AlignCenter)
        p.end()


class RankedBars(Chart):
    """A short ranked list (top tasks): label, thin bar, time."""

    def __init__(self, title: str, accent: str = "#2dd4bf", parent: QWidget | None = None):
        super().__init__(title, 204, parent)
        self.rows: list[tuple[str, float]] = []
        self.accent = QColor(accent)

    def set_data(self, rows: list[tuple[str, float]], accent: str) -> None:
        self.rows, self.accent = rows, QColor(accent)
        self.update()

    def paintEvent(self, _ev) -> None:  # noqa: N802
        p, body = self.begin()
        if not self.rows:
            self.empty(p, body, "Tick tasks while you focus and they show up here")
            p.end()
            return
        peak = self.rows[0][1]
        row_h = min(30.0, body.height() / max(len(self.rows), 1))
        y = body.top()
        for name, secs in self.rows:
            label = QFontMetrics(_font(12)).elidedText(name, Qt.ElideRight, int(body.width() * 0.45))
            self.text(p, label, QRectF(body.left(), y, body.width() * 0.45, row_h), 12, TEXT)
            track = QRectF(body.left() + body.width() * 0.47, y + row_h / 2 - 3, body.width() * 0.37, 6)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(theme.RAISED))
            p.drawRoundedRect(track, 3, 3)
            p.setBrush(self.accent)
            p.drawRoundedRect(QRectF(track.left(), track.top(), max(4.0, track.width() * secs / peak), 6), 3, 3)
            self.text(p, fmt_duration(secs), QRectF(body.right() - 60, y, 60, row_h), 12, DIM, Qt.AlignRight | Qt.AlignVCenter)
            self._hits.append((QRectF(body.left(), y, body.width(), row_h), f"{name}: {fmt_duration(secs)}"))
            y += row_h
        p.end()
