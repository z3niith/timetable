# Timetable

An interval timer that floats over your screen, **always on top and click-through**, so you can see
where you are in a study or work session without it ever getting in the way. Drawn natively with Qt,
not an embedded web page.

Inspired by the original Timeline Timer HUD, which is no longer maintained. Not affiliated with it.

## Features

- **Click-through HUD** docked to the top or bottom of the screen. Mouse clicks pass straight to the app underneath.
- **Always on top**, hidden from the taskbar. Lives in the system tray.
- **Timeline view**: every interval is a segment sized by its length, with a progress line and playhead.
- **Compact mode**: a thin line with small labels and a countdown, on a clear background by default (adjustable in Settings).
- **Ding** at the end of every interval, and a three-note chime when the whole agenda finishes. Volume and a custom `.wav` are in Settings.
- **Warning pulse**: the countdown flashes amber in the last 30 seconds (configurable).
- **Sessions**: save named agendas ("Chemistry study", "Deep work") and pick one from the tray menu or the Sessions window.
- **To-do list per session**: the HUD shows your current task, and a hotkey ticks it off.
- **Live editing**: change the agenda or tasks while the timer runs.
- **History log**: every finished or skipped interval is recorded locally, ready for a future history view.
- **Global hotkeys** so you never need to click it.

## Run it

**Installer (recommended):** download `Timetable-Setup-<version>.exe` from the
[Releases page](https://github.com/z3niith/timetable/releases). It installs for your user only, with no admin prompt.
Once the winget package is accepted: `winget install z3niith.Timetable`.

**From source:** you need Python 3.10 or newer on Windows.

```powershell
python -m pip install -r requirements.txt
python -m timetable
```

An icon appears in the system tray. On Windows 11 it may be tucked behind the `^` arrow; drag it out to pin it.

## Sessions, agendas and tasks

A **session** is a name, an agenda and a to-do list. Open **Sessions...** from the tray (or `Ctrl+Alt+E`) to choose
your session, create a new one, duplicate, rename or delete it. Switching sessions restarts the timer, and asks first
if it is part-way through. Everything you type is saved straight away.

**Agenda:** one interval per line, a name then a length. Lengths can be `50m`, `1h30m`, `45s`, or a bare number (minutes).
Names starting with Break, Rest, Lunch or Pause are drawn as breaks. Lines starting with `#` are ignored.
See [`examples/study-agenda.txt`](examples/study-agenda.txt).

**Tasks:** one per line. Start a line with `[x]` if it is done. The first unfinished task is shown on the HUD
(next to the session name, or top-right in compact mode). `Ctrl+Alt+Enter` ticks it and moves to the next.

## Controls

Click-through means the HUD can't receive clicks, so control it from the tray or with hotkeys.
Switch on **Interactive mode** (tray menu, or `Ctrl+Alt+L`) to get a row of buttons on the HUD, then switch it off to go back to click-through.

| Hotkey | Action |
| --- | --- |
| `Ctrl+Alt+Space` | Start / pause |
| `Ctrl+Alt+Right` | Skip interval |
| `Ctrl+Alt+R` | Restart |
| `Ctrl+Alt+Up` / `Down` | +1 / -1 minute on the current interval |
| `Ctrl+Alt+C` | Compact mode |
| `Ctrl+Alt+L` | Interactive mode (unlock / lock) |
| `Ctrl+Alt+Enter` | Tick the current task |
| `Ctrl+Alt+Backspace` | Undo the last tick |
| `Ctrl+Alt+E` | Sessions window |

Tray icon: left-click toggles start/pause, double-click toggles interactive mode, right-click opens the menu.
If another program already owns a hotkey, that one is skipped.

Your data lives in `%APPDATA%\Timetable\`:

| File | Contents |
| --- | --- |
| `settings.json` | Appearance, sound and behaviour settings |
| `sessions.json` | Your sessions: agendas and tasks |
| `history.jsonl` | One line per finished or skipped interval (time, session, interval, planned and actual seconds) |

## Development

```powershell
pip install -r requirements.txt pytest ruff
python -m pytest
ruff check .
```

The timer logic (`engine.py`, `agenda.py`) has no GUI dependency and is unit tested.

## Releasing

1. Run the **Build installer** workflow manually (Actions tab) to check it builds. It attaches the installer to the run.
2. Tag and push: `git tag v0.1.1 && git push origin v0.1.1`. The workflow builds the installer and publishes a GitHub Release.
3. Copy the SHA256 printed in the workflow log, then publish to winget:
   ```powershell
   winget install wingetcreate
   wingetcreate update z3niith.Timetable --version 0.1.1 --urls https://github.com/z3niith/timetable/releases/download/v0.1.1/Timetable-Setup-0.1.1.exe --submit
   ```
   For the very first submission use `wingetcreate new <installer url>`, or fill in the templates under `winget/`.

## Ideas for later

Round clock style, a kanban board per session, a history window with stats and a heatmap, left/right docking, multi-monitor choice, per-interval colours, seeking by clicking the timeline.

## License

MIT
