"""Regenerates assets/icon.ico from the tray icon drawing. Run: python tools/make_icon.py"""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # pip install pillow
from PySide6.QtGui import QGuiApplication

from timetable.app import make_icon

app = QGuiApplication([])
pm = make_icon("#2dd4bf").pixmap(256, 256)
png = Path(__file__).resolve().parent.parent / "assets" / "icon.png"
pm.save(str(png))
Image.open(png).save(png.with_suffix(".ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("wrote", png.with_suffix(".ico"))
