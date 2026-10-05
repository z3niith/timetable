"""Launcher used for the packaged exe. Run from source with: python -m timetable"""
import sys

from timetable.app import main

if __name__ == "__main__":
    sys.exit(main())
