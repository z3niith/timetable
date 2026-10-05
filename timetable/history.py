"""Quiet log of every interval that ends or is skipped, kept for a future history view.

One JSON object per line in history.jsonl, so it is easy to append to and to read back.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .agenda import Item
from .settings import config_dir


class HistoryLog:
    def __init__(self, path: Path | None = None):
        self.path = path or (config_dir() / "history.jsonl")

    def add(self, session_id: str, session_name: str, item: Item, event: str, spent: float) -> None:
        """event is 'completed' (ran to the end) or 'skipped'. spent is seconds actually run."""
        record = {
            "time": datetime.now().astimezone().isoformat(timespec="seconds"),
            "session_id": session_id,
            "session": session_name,
            "interval": item.name,
            "is_break": item.is_break,
            "planned_seconds": round(item.seconds),
            "spent_seconds": round(spent),
            "event": event,
        }
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except OSError:
            pass  # logging must never interrupt the timer

    def read(self) -> list[dict]:
        records: list[dict] = []
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return records
        for line in lines:
            try:
                records.append(json.loads(line))
            except ValueError:
                continue  # skip a damaged line instead of losing the whole log
        return records
