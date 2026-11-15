"""One dark look for every window, matching the HUD's navy and accent colour."""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

BG = "#0b1220"
SURFACE = "#111b2e"
RAISED = "#17233a"
BORDER = "#22304a"
TEXT = "#e8eef6"
DIM = "#8a98ac"
FAINT = "#586680"


def build_stylesheet(accent: str) -> str:
    return f"""
    QWidget {{ color: {TEXT}; font-size: 13px; }}
    QDialog, QMainWindow {{ background: {BG}; }}
    QLabel {{ background: transparent; }}
    QLabel[muted="true"] {{ color: {DIM}; }}
    QToolTip {{ background: {RAISED}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px 6px; }}
    QPushButton {{ background: {RAISED}; border: 1px solid {BORDER}; border-radius: 8px; padding: 6px 14px; }}
    QPushButton:hover {{ border-color: {accent}; }}
    QPushButton:pressed {{ background: {SURFACE}; }}
    QPushButton:checked {{ background: {accent}; color: #04121a; border-color: {accent}; }}
    QPushButton:focus {{ border-color: {accent}; }}
    QPlainTextEdit, QLineEdit, QSpinBox, QComboBox {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 5px 8px;
        selection-background-color: {accent}; selection-color: #04121a; }}
    QPlainTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color: {accent}; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox QAbstractItemView {{ background: {RAISED}; border: 1px solid {BORDER};
        selection-background-color: {accent}; selection-color: #04121a; outline: 0; }}
    QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}
    QCheckBox {{ spacing: 8px; background: transparent; }}
    QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 5px; border: 1px solid {FAINT}; background: {SURFACE}; }}
    QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {BORDER}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {accent}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {TEXT}; width: 14px; height: 14px; margin: -6px 0; border-radius: 7px; }}
    QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; top: -1px; background: {BG}; }}
    QTabBar {{ background: transparent; }}
    QTabBar::tab {{ background: transparent; color: {DIM}; padding: 8px 18px; border: none; border-bottom: 2px solid transparent; }}
    QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {accent}; }}
    QTabBar::tab:hover {{ color: {TEXT}; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 5px; min-height: 24px; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QMenu {{ background: {RAISED}; border: 1px solid {BORDER}; padding: 4px; border-radius: 8px; }}
    QMenu::item {{ padding: 6px 22px; border-radius: 5px; }}
    QMenu::item:selected {{ background: {BORDER}; }}
    QMenu::separator {{ height: 1px; background: {BORDER}; margin: 4px 8px; }}
    QMessageBox {{ background: {BG}; }}
    """


def apply_theme(app: QApplication, accent: str) -> None:
    """Fusion + a dark palette + the stylesheet; call again when the accent changes."""
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor(SURFACE))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.Button, QColor(RAISED))
    pal.setColor(QPalette.ButtonText, QColor(TEXT))
    pal.setColor(QPalette.Highlight, QColor(accent))
    pal.setColor(QPalette.HighlightedText, QColor("#04121a"))
    app.setPalette(pal)
    app.setStyleSheet(build_stylesheet(accent))
