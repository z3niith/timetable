"""Timer engine. No GUI code here, so it is easy to test."""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable

from .agenda import Item


class State(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class TimerEngine:
    """Walks through a list of items. Call :meth:`tick` regularly."""

    def __init__(self, items: list[Item], clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self.items = items
        self.index = 0
        self.elapsed = 0.0  # seconds elapsed inside the current item
        self.state = State.IDLE
        self._last = 0.0
        # Set by the UI: called with (finished item, was_last)
        self.on_interval_end: Callable[[Item, bool], None] = lambda item, last: None

    @property
    def current(self) -> Item | None:
        return self.items[self.index] if 0 <= self.index < len(self.items) else None

    @property
    def remaining(self) -> float:
        cur = self.current
        return max(0.0, cur.seconds - self.elapsed) if cur else 0.0

    @property
    def total(self) -> float:
        return sum(i.seconds for i in self.items)

    @property
    def passed(self) -> float:
        if self.state is State.FINISHED:
            return self.total
        return sum(i.seconds for i in self.items[: self.index]) + self.elapsed

    @property
    def total_remaining(self) -> float:
        return max(0.0, self.total - self.passed)

    def start(self) -> None:
        if self.state is State.FINISHED:
            self.restart()
        if not self.items:
            return
        self._last = self._clock()
        self.state = State.RUNNING

    def pause(self) -> None:
        if self.state is State.RUNNING:
            self.tick()
            self.state = State.PAUSED

    def toggle(self) -> None:
        if self.state is State.RUNNING:
            self.pause()
        else:
            self.start()

    def restart(self) -> None:
        self.index = 0
        self.elapsed = 0.0
        self.state = State.IDLE

    def skip(self) -> None:
        """Jump to the next interval without a ding."""
        if self.state is State.FINISHED or not self.items:
            return
        if self.index >= len(self.items) - 1:
            self.state = State.FINISHED
            return
        self.index += 1
        self.elapsed = 0.0
        self._last = self._clock()

    def adjust(self, delta_seconds: float) -> None:
        """Lengthen or shorten the current interval (never below elapsed + 1s)."""
        cur = self.current
        if cur is None or self.state is State.FINISHED:
            return
        cur.seconds = max(self.elapsed + 1, cur.seconds + delta_seconds)

    def set_items(self, items: list[Item]) -> None:
        """Swap in a new agenda while keeping position where possible."""
        self.items = items
        if not items:
            self.restart()
            return
        if self.index >= len(items):
            self.index = len(items) - 1
            self.elapsed = 0.0
        if self.elapsed >= items[self.index].seconds:
            self.elapsed = max(0.0, items[self.index].seconds - 1)
        if self.state is State.FINISHED:
            self.state = State.IDLE

    def tick(self) -> None:
        if self.state is not State.RUNNING:
            return
        now = self._clock()
        self.elapsed += now - self._last
        self._last = now
        # A long stall (sleep/hibernate) can cross several intervals, so loop.
        while self.state is State.RUNNING and self.current and self.elapsed >= self.current.seconds:
            finished = self.current
            self.elapsed -= finished.seconds
            last = self.index >= len(self.items) - 1
            if last:
                self.elapsed = 0.0
                self.state = State.FINISHED
            else:
                self.index += 1
            self.on_interval_end(finished, last)
