"""The always-on-top HUD, painted natively with QPainter (no web view)."""

from __future__ import annotations

import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .agenda import format_clock, format_short
from .engine import State, TimerEngine
from .settings import Settings

FULL_H, COMPACT_H, BUTTON_ROW = 86, 46, 32

TEXT = QColor(232, 238, 246)
DIM = QColor(138, 152, 172)
FAINT = QColor(88, 102, 124)
WARN = QColor(251, 191, 36)


class Hud(QWidget):
    """Emits ``action(name)`` when a button is clicked in interactive mode."""

    action = Signal(str)

    def __init__(self, engine: TimerEngine, settings: Settings):
        super().__init__()
        self.engine, self.s = engine, settings
        self._flags = None
        self._buttons: dict[str, QRectF] = {}
        self._hover = ""
        self._clear = False
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setWindowTitle("Timetable")
        self._ticker = QTimer(self, interval=100)
        self._ticker.timeout.connect(self._on_tick)
        self._ticker.start()
        self.apply_window_state()

    # -- window behaviour -------------------------------------------------
    def apply_window_state(self) -> None:
        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.WindowDoesNotAcceptFocus
        if self.s.keep_on_top:
            flags |= Qt.WindowStaysOnTopHint
        if self.s.click_through:
            flags |= Qt.WindowTransparentForInput
        if flags != self._flags:
            self._flags = flags
            self.setWindowFlags(flags)
        self.reposition()
        self.show()

    def reposition(self) -> None:
        h = (COMPACT_H if self.s.compact else FULL_H) + (0 if self.s.click_through else BUTTON_ROW)
        screen = QGuiApplication.primaryScreen()
        g = screen.availableGeometry()
        m = max(0, self.s.margin)
        y = g.top() + m if self.s.dock == "top" else g.bottom() + 1 - h - m
        self.setGeometry(g.left(), y, g.width(), h)

    def _on_tick(self) -> None:
        self.engine.tick()
        if self.engine.state is State.RUNNING:
            self.update()

    # -- fonts ------------------------------------------------------------
    @staticmethod
    def _font(px: float, bold: bool = False, mono: bool = False) -> QFont:
        f = QFont()
        f.setFamilies(["Cascadia Mono", "Consolas", "monospace"] if mono else ["Segoe UI Variable", "Segoe UI", "Inter", "sans-serif"])
        f.setPixelSize(int(px))
        f.setWeight(QFont.Bold if bold else QFont.Normal)
        return f

    # -- painting ---------------------------------------------------------
    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        w, h = self.width(), self.height()
        compact = self.s.compact
        e = self.engine
        accent = QColor(self.s.accent)

        opacity = self.s.compact_opacity if compact else self.s.opacity
        opacity = max(0.0, min(1.0, opacity))
        # On a clear background, text and lines need their own backing to stay readable.
        self._clear = opacity < 0.5
        if opacity > 0:
            bg = QColor(8, 14, 26)
            bg.setAlphaF(opacity)
            p.setPen(QPen(QColor(255, 255, 255, int(24 * opacity)), 1))
            p.setBrush(bg)
            p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), 10, 10)

        base_h = COMPACT_H if compact else FULL_H
        line_y = 15 if compact else 56
        left = 20.0
        right = w - (150.0 if compact else 24.0)
        total = e.total
        if total <= 0:
            self._text(p, "Agenda is empty. Right-click the tray icon > Edit agenda.", QRectF(0, 0, w, base_h), self._font(12), DIM, Qt.AlignCenter)
            self._draw_buttons(p, base_h, accent)
            return

        def x_at(t: float) -> float:
            return left + (right - left) * (t / total)

        # headline (full mode) or right-hand clock (compact mode)
        countdown = format_clock(e.remaining)
        pulse = (
            self.s.warn_seconds > 0 and e.state is State.RUNNING
            and e.remaining <= self.s.warn_seconds and int(time.monotonic() * 2) % 2 == 0
        )
        clock_color = WARN if pulse else (TEXT if e.state is State.RUNNING else DIM)
        cur = e.current
        if e.state is State.FINISHED:
            countdown, name = "Done", "Agenda complete"
        else:
            name = cur.name if cur else ""
        passed_bits = []
        if self.s.show_passed:
            passed_bits.append(f"Passed {format_clock(e.passed)}")
        if self.s.show_remaining:
            passed_bits.append(f"Left {format_clock(e.total_remaining)}")
        passed_text = "   ".join(passed_bits)

        if compact:
            self._text(p, countdown, QRectF(w - 150, 14, 132, 28), self._font(20, True, True), clock_color, Qt.AlignRight | Qt.AlignVCenter)
            if passed_text:
                self._text(p, passed_text, QRectF(w - 220, 2, 202, 16), self._font(10, mono=True), FAINT, Qt.AlignRight | Qt.AlignVCenter)
        else:
            self._text(p, "Timetable", QRectF(20, 0, 200, 38), self._font(11, True), DIM, Qt.AlignLeft | Qt.AlignVCenter)
            f_name, f_clock = self._font(13), self._font(22, True, True)
            nw = QFontMetrics(f_name).horizontalAdvance(name)
            cw = QFontMetrics(f_clock).horizontalAdvance(countdown)
            x0 = (w - (nw + 14 + cw)) / 2
            self._text(p, name, QRectF(x0, 0, nw + 4, 38), f_name, DIM, Qt.AlignLeft | Qt.AlignVCenter)
            self._text(p, countdown, QRectF(x0 + nw + 14, 0, cw + 8, 38), f_clock, clock_color, Qt.AlignLeft | Qt.AlignVCenter)
            if passed_text:
                self._text(p, passed_text, QRectF(w - 320, 0, 300, 38), self._font(11, mono=True), DIM, Qt.AlignRight | Qt.AlignVCenter)

        # segments
        t0 = 0.0
        play_x = x_at(e.passed)
        for i, item in enumerate(e.items):
            x0, x1 = x_at(t0), x_at(t0 + item.seconds)
            track = QColor(66, 80, 102) if item.is_break else QColor(170, 183, 201)
            if self._clear:
                p.setPen(QPen(QColor(0, 0, 0, 150), 5, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(x0, line_y), QPointF(x1, line_y))
                if item.is_break:
                    track = QColor(120, 134, 156)
            p.setPen(QPen(track, 2, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(QPointF(x0, line_y), QPointF(x1, line_y))
            if i < e.index or e.state is State.FINISHED:
                ratio = 1.0
            elif i == e.index:
                ratio = min(1.0, e.elapsed / item.seconds)
            else:
                ratio = 0.0
            if ratio > 0:
                p.setPen(QPen(accent, 3, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(x0, line_y), QPointF(x0 + (x1 - x0) * ratio, line_y))
            self._label(p, item, i, x0, x1, line_y, compact, accent)
            t0 += item.seconds

        # boundary nodes, then the playhead on top
        t0 = 0.0
        p.setPen(Qt.NoPen)
        for k in range(len(e.items) + 1):
            x = x_at(t0)
            p.setBrush(accent if x <= play_x + 0.5 else QColor(200, 210, 224))
            p.drawEllipse(QPointF(x, line_y), 3, 3)
            if k < len(e.items):
                t0 += e.items[k].seconds
        halo = QColor(accent)
        halo.setAlpha(60)
        p.setBrush(halo)
        p.drawEllipse(QPointF(play_x, line_y), 9, 9)
        p.setBrush(accent)
        p.drawRoundedRect(QRectF(play_x - 4.5, line_y - 4.5, 9, 9), 2, 2)

        self._draw_buttons(p, base_h, accent)

    def _label(self, p, item, i, x0, x1, line_y, compact, accent) -> None:
        width = x1 - x0
        is_cur = i == self.engine.index and self.engine.state is not State.FINISHED
        colour = TEXT if is_cur else (FAINT if item.is_break else DIM)
        name = item.name
        narrow = width < (46 if compact else 64)
        if narrow:
            name = format_short(item.seconds)  # too tight for a name: show the length instead
        if compact:
            if not narrow and len(name) > self.s.compact_label_len:
                name = name[: self.s.compact_label_len] + "..."
            f = self._font(11)
            fm = QFontMetrics(f)
            text = name if narrow else fm.elidedText(name, Qt.ElideRight, int(max(10, width - 16)))
            cw = fm.horizontalAdvance(text) + 14
            rect = QRectF((x0 + x1) / 2 - cw / 2, line_y + 7, cw, 20)
            p.setPen(Qt.NoPen)
            if self._clear:
                p.setBrush(QColor(8, 14, 26, 170))
                p.drawRoundedRect(rect, 5, 5)
            chip = QColor(accent) if is_cur else QColor(255, 255, 255)
            chip.setAlpha(46 if is_cur else 14)
            p.setBrush(chip)
            p.drawRoundedRect(rect, 5, 5)
            self._text(p, text, rect, f, colour, Qt.AlignCenter)
            return
        f_name, f_dur = self._font(12, is_cur), self._font(10)
        fm_n, fm_d = QFontMetrics(f_name), QFontMetrics(f_dur)
        dur = format_short(item.seconds)
        avail = max(8, width - 10)
        text = fm_n.elidedText(name, Qt.ElideRight, int(avail))
        dw = fm_d.horizontalAdvance(dur)
        show_dur = not narrow and fm_n.horizontalAdvance(text) + 6 + dw <= avail
        total_w = fm_n.horizontalAdvance(text) + (6 + dw if show_dur else 0)
        x = (x0 + x1) / 2 - total_w / 2
        y = line_y + 10
        self._text(p, text, QRectF(x, y, fm_n.horizontalAdvance(text) + 2, 20), f_name, colour, Qt.AlignLeft | Qt.AlignVCenter)
        if show_dur:
            self._text(p, dur, QRectF(x + fm_n.horizontalAdvance(text) + 6, y, dw + 2, 20), f_dur, FAINT, Qt.AlignLeft | Qt.AlignVCenter)

    def _text(self, p, text, rect, font, colour, align) -> None:
        p.setFont(font)
        if getattr(self, "_clear", False):
            p.setPen(QColor(0, 0, 0, 200))
            for dx, dy in ((1, 1), (-1, 1), (0, 2)):
                p.drawText(rect.translated(dx, dy), int(align), text)
        p.setPen(colour)
        p.drawText(rect, int(align), text)

    # -- interactive mode buttons ------------------------------------------
    def _draw_buttons(self, p, base_h, accent) -> None:
        self._buttons = {}
        if self.s.click_through:
            return
        running = self.engine.state is State.RUNNING
        specs = [
            ("toggle", "Pause" if running else "Start"), ("restart", "Restart"),
            ("minus", "-1 min"), ("plus", "+1 min"), ("skip", "Skip"),
            ("agenda", "Agenda"), ("compact", "Compact"), ("settings", "Settings"),
            ("lock", "Lock (click-through)"),
        ]
        f = self._font(11)
        fm = QFontMetrics(f)
        x, y = 20.0, base_h + 3.0
        for key, label in specs:
            wid = fm.horizontalAdvance(label) + 22
            rect = QRectF(x, y, wid, 24)
            self._buttons[key] = rect
            hot = key == self._hover
            fill = QColor(accent if key == "toggle" else QColor(255, 255, 255))
            fill.setAlpha(70 if hot else (40 if key == "toggle" else 16))
            p.setPen(QPen(QColor(255, 255, 255, 28), 1))
            p.setBrush(fill)
            p.drawRoundedRect(rect, 6, 6)
            self._text(p, label, rect, f, TEXT, Qt.AlignCenter)
            x += wid + 8

    def _hit(self, pos) -> str:
        for key, rect in self._buttons.items():
            if rect.contains(QPointF(pos)):
                return key
        return ""

    def mouseMoveEvent(self, ev) -> None:  # noqa: N802
        key = self._hit(ev.position())
        if key != self._hover:
            self._hover = key
            self.update()

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        key = self._hit(ev.position())
        if key and ev.button() == Qt.LeftButton:
            self.action.emit(key)

    def leaveEvent(self, _ev) -> None:  # noqa: N802
        self._hover = ""
        self.update()
