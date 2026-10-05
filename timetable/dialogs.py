"""Agenda editor and settings windows. These are normal windows, so they are clickable."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSlider, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from .agenda import format_short, parse_agenda
from .sessions import format_tasks, parse_tasks
from .settings import Settings


class SessionDialog(QDialog):
    """Pick, create and edit sessions. Every edit is applied to the running timer straight away.

    This window only shows things and emits signals; the controller owns the data.
    """

    switch_requested = Signal(str)
    new_requested = Signal()
    duplicate_requested = Signal()
    rename_requested = Signal()
    delete_requested = Signal()
    agenda_changed = Signal(str)
    tasks_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Sessions")
        self.resize(560, 560)

        self.combo = QComboBox()
        new, dup = QPushButton("New"), QPushButton("Duplicate")
        ren, dele = QPushButton("Rename"), QPushButton("Delete")
        top = QHBoxLayout()
        top.addWidget(QLabel("Choose your session"))
        top.addWidget(self.combo, 1)
        for b in (new, dup, ren, dele):
            top.addWidget(b)

        mono = QFont("Cascadia Mono")
        mono.setStyleHint(QFont.Monospace)
        self.agenda = QPlainTextEdit()
        self.agenda.setFont(mono)
        self.tasks = QPlainTextEdit()
        self.tasks.setFont(mono)
        self.tasks.setPlaceholderText("Read chapter 3\nPractice problems\n[x] Already done")
        self.agenda_status, self.tasks_status = QLabel(), QLabel()

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab(
            "One interval per line: a name, then a length like 50m, 1h30m, 45s. "
            "A bare number means minutes. Lines starting with # are ignored.",
            self.agenda, self.agenda_status), "Agenda")
        self.tabs.addTab(self._tab(
            "Your to-do list for this session, one task per line. Start a line with [x] if it is done. "
            "Tick the next task from the HUD or with Ctrl+Alt+Enter.",
            self.tasks, self.tasks_status), "Tasks")

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.tabs)

        self.combo.activated.connect(lambda i: self.switch_requested.emit(self.combo.itemData(i)))
        new.clicked.connect(self.new_requested)
        dup.clicked.connect(self.duplicate_requested)
        ren.clicked.connect(self.rename_requested)
        dele.clicked.connect(self.delete_requested)
        self.agenda.textChanged.connect(self._agenda_edited)
        self.tasks.textChanged.connect(self._tasks_edited)

    @staticmethod
    def _tab(hint: str, editor: QPlainTextEdit, status: QLabel) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        label = QLabel(hint)
        label.setWordWrap(True)
        lay.addWidget(label)
        lay.addWidget(editor)
        lay.addWidget(status)
        return page

    def refresh(self, store) -> None:
        """Show the store's current state without triggering edit signals."""
        self.combo.blockSignals(True)
        self.combo.clear()
        for session in store.sessions:
            self.combo.addItem(session.name, session.id)
        self.combo.setCurrentIndex(max(0, self.combo.findData(store.current_id)))
        self.combo.blockSignals(False)
        self._set(self.agenda, store.current.agenda)
        self._set(self.tasks, format_tasks(store.current.tasks))
        self._update_status()

    @staticmethod
    def _set(editor: QPlainTextEdit, text: str) -> None:
        if editor.toPlainText() != text:
            editor.blockSignals(True)
            editor.setPlainText(text)
            editor.blockSignals(False)

    def _update_status(self) -> None:
        items = parse_agenda(self.agenda.toPlainText())
        total = sum(i.seconds for i in items)
        self.agenda_status.setText(f"{len(items)} intervals, {format_short(total)} total" if items else "No valid intervals yet")
        tasks = parse_tasks(self.tasks.toPlainText())
        done = sum(t.done for t in tasks)
        self.tasks_status.setText(f"{done} of {len(tasks)} done" if tasks else "No tasks")

    def _agenda_edited(self) -> None:
        self._update_status()
        self.agenda_changed.emit(self.agenda.toPlainText())

    def _tasks_edited(self) -> None:
        self._update_status()
        self.tasks_changed.emit(self.tasks.toPlainText())


class SettingsDialog(QDialog):
    changed = Signal()

    def __init__(self, s: Settings, test_sound, parent: QWidget | None = None):
        super().__init__(parent)
        self.s = s
        self.setWindowTitle("Timetable settings")
        form = QFormLayout(self)

        self.dock = QComboBox()
        self.dock.addItems(["Top", "Bottom"])
        self.dock.setCurrentIndex(0 if s.dock == "top" else 1)
        self.margin = self._spin(0, 300, s.margin, " px")
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(int(s.opacity * 100))
        self.compact_opacity = QSlider(Qt.Horizontal)
        self.compact_opacity.setRange(0, 100)
        self.compact_opacity.setValue(int(s.compact_opacity * 100))
        self.accent = QPushButton()
        self._paint_accent()
        self.label_len = self._spin(4, 60, s.compact_label_len, " chars")
        self.passed = QCheckBox("Show total passed time")
        self.passed.setChecked(s.show_passed)
        self.remaining = QCheckBox("Show total remaining time")
        self.remaining.setChecked(s.show_remaining)
        self.on_top = QCheckBox("Keep above other windows")
        self.on_top.setChecked(s.keep_on_top)
        self.warn = self._spin(0, 600, s.warn_seconds, " s (0 = off)")

        self.ding = QCheckBox("Play a ding at the end of each interval")
        self.ding.setChecked(s.ding_enabled)
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(s.volume * 100))
        self.sound = QLineEdit(s.sound_file)
        self.sound.setPlaceholderText("Default ding (or choose a .wav file)")
        browse, test = QPushButton("Browse..."), QPushButton("Test")
        row = QHBoxLayout()
        row.addWidget(self.sound)
        row.addWidget(browse)
        row.addWidget(test)
        self.autostart = QCheckBox("Start with Windows")
        self.autostart.setChecked(s.autostart)

        form.addRow("Dock edge", self.dock)
        form.addRow("Edge margin", self.margin)
        form.addRow("Background opacity (full)", self.opacity)
        form.addRow("Background opacity (compact)", self.compact_opacity)
        form.addRow("Accent colour", self.accent)
        form.addRow("Compact label length", self.label_len)
        form.addRow(self.passed)
        form.addRow(self.remaining)
        form.addRow(self.on_top)
        form.addRow("Warning pulse", self.warn)
        form.addRow(self.ding)
        form.addRow("Volume", self.volume)
        form.addRow("Custom sound", row)
        form.addRow(self.autostart)

        for sig in (self.dock.currentIndexChanged, self.margin.valueChanged, self.opacity.valueChanged, self.compact_opacity.valueChanged,
                    self.label_len.valueChanged, self.passed.toggled, self.remaining.toggled,
                    self.on_top.toggled, self.warn.valueChanged, self.ding.toggled,
                    self.volume.valueChanged, self.sound.editingFinished, self.autostart.toggled):
            sig.connect(self._apply)
        self.accent.clicked.connect(self._pick_colour)
        browse.clicked.connect(self._browse)
        test.clicked.connect(test_sound)

    @staticmethod
    def _spin(lo, hi, val, suffix) -> QSpinBox:
        sp = QSpinBox()
        sp.setRange(lo, hi)
        sp.setValue(val)
        sp.setSuffix(suffix)
        return sp

    def _paint_accent(self) -> None:
        self.accent.setText(self.s.accent)
        self.accent.setStyleSheet(f"background:{self.s.accent}; color:#000; padding:4px 12px;")

    def _pick_colour(self) -> None:
        c = QColorDialog.getColor(QColor(self.s.accent), self, "Accent colour")
        if c.isValid():
            self.s.accent = c.name()
            self._paint_accent()
            self.changed.emit()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose a ding sound", "", "WAV audio (*.wav)")
        if path:
            self.sound.setText(path)
            self._apply()

    def _apply(self) -> None:
        s = self.s
        s.dock = "top" if self.dock.currentIndex() == 0 else "bottom"
        s.margin = self.margin.value()
        s.opacity = self.opacity.value() / 100
        s.compact_opacity = self.compact_opacity.value() / 100
        s.compact_label_len = self.label_len.value()
        s.show_passed, s.show_remaining = self.passed.isChecked(), self.remaining.isChecked()
        s.keep_on_top = self.on_top.isChecked()
        s.warn_seconds = self.warn.value()
        s.ding_enabled = self.ding.isChecked()
        s.volume = self.volume.value() / 100
        s.sound_file = self.sound.text().strip()
        s.autostart = self.autostart.isChecked()
        self.changed.emit()
