"""Sessions: a named agenda plus a to-do list, saved in sessions.json."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .settings import DEFAULT_AGENDA, config_dir

_TASK_LINE = re.compile(r"^(?:[-*]\s*)?(?:\[(?P<mark>[ xX])\]\s*)?(?P<text>\S.*)$")


@dataclass
class Task:
    text: str
    done: bool = False


def parse_tasks(text: str) -> list[Task]:
    """One task per line. '[x] text' is done, '[ ] text' or plain 'text' is open."""
    tasks: list[Task] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _TASK_LINE.match(line)
        if m:
            tasks.append(Task(m.group("text").strip(), (m.group("mark") or " ") in "xX"))
    return tasks


def format_tasks(tasks: list[Task]) -> str:
    return "\n".join(f"[{'x' if t.done else ' '}] {t.text}" for t in tasks)


@dataclass
class Session:
    id: str
    name: str
    agenda: str = DEFAULT_AGENDA
    tasks: list[Task] = field(default_factory=list)

    @property
    def current_task(self) -> Task | None:
        return next((t for t in self.tasks if not t.done), None)

    def tick_task(self) -> bool:
        """Mark the first open task done. Returns False if there was none."""
        task = self.current_task
        if task is None:
            return False
        task.done = True
        return True

    def untick_task(self) -> bool:
        """Re-open the most recently finished task. Returns False if none are done."""
        for task in reversed(self.tasks):
            if task.done:
                task.done = False
                return True
        return False


class SessionStore:
    """All saved sessions and which one is selected. Every change is saved straight away."""

    def __init__(self, path: Path | None = None, legacy_agenda: str | None = None):
        self.path = path or (config_dir() / "sessions.json")
        self.sessions: list[Session] = []
        self.current_id = ""
        if not self._load():
            first = Session(_new_id(), "My session", legacy_agenda or DEFAULT_AGENDA)
            self.sessions, self.current_id = [first], first.id
            self.save()

    # -- lookup ---------------------------------------------------------
    @property
    def current(self) -> Session:
        return self.get(self.current_id) or self.sessions[0]

    def get(self, session_id: str) -> Session | None:
        return next((s for s in self.sessions if s.id == session_id), None)

    # -- changes --------------------------------------------------------
    def create(self, name: str, agenda: str = DEFAULT_AGENDA, tasks: list[Task] | None = None) -> Session:
        session = Session(_new_id(), self._unique_name(name.strip() or "New session"), agenda, tasks or [])
        self.sessions.append(session)
        self.save()
        return session

    def duplicate(self, session_id: str) -> Session | None:
        src = self.get(session_id)
        if src is None:
            return None
        copy = [Task(t.text, False) for t in src.tasks]
        return self.create(f"{src.name} copy", src.agenda, copy)

    def rename(self, session_id: str, name: str) -> None:
        session = self.get(session_id)
        name = name.strip()
        if session and name and name != session.name:
            session.name = self._unique_name(name, ignore=session)
            self.save()

    def delete(self, session_id: str) -> bool:
        """Delete a session. The last remaining one can't be deleted."""
        if len(self.sessions) <= 1 or self.get(session_id) is None:
            return False
        self.sessions = [s for s in self.sessions if s.id != session_id]
        if self.current_id == session_id:
            self.current_id = self.sessions[0].id
        self.save()
        return True

    def select(self, session_id: str) -> None:
        if self.get(session_id):
            self.current_id = session_id
            self.save()

    def _unique_name(self, name: str, ignore: Session | None = None) -> str:
        taken = {s.name.lower() for s in self.sessions if s is not ignore}
        candidate, n = name, 2
        while candidate.lower() in taken:
            candidate = f"{name} {n}"
            n += 1
        return candidate

    # -- disk -----------------------------------------------------------
    def _load(self) -> bool:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            sessions = [
                Session(
                    str(s["id"]), str(s["name"]), str(s.get("agenda", "")),
                    [Task(str(t["text"]), bool(t.get("done"))) for t in s.get("tasks", [])],
                )
                for s in data["sessions"]
            ]
        except (OSError, ValueError, KeyError, TypeError):
            return False
        if not sessions:
            return False
        self.sessions = sessions
        self.current_id = str(data.get("current", sessions[0].id))
        return True

    def save(self) -> None:
        data = {
            "version": 1,
            "current": self.current_id,
            "sessions": [
                {
                    "id": s.id, "name": s.name, "agenda": s.agenda,
                    "tasks": [{"text": t.text, "done": t.done} for t in s.tasks],
                }
                for s in self.sessions
            ],
        }
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(self.path)  # atomic: a crash can't leave a half-written file
        except OSError:
            pass


def _new_id() -> str:
    return uuid.uuid4().hex[:8]
