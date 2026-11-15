# Timetable

An interval timer that floats over your screen, **always on top and click-through**, so you can see where you are in a
study or work session without it ever getting in the way. Built for focus, including with ADHD.

![The Timetable HUD docked to the top of the screen](assets/screenshots/hud.png)

## Install

```powershell
winget install z3niith.Timetable
```

Or download `Timetable-Setup-<version>.exe` from the [Releases page](https://github.com/z3niith/timetable/releases).
It installs for your user only, with no admin prompt.

An icon appears in the system tray. On Windows 11 it may be tucked behind the `^` arrow; drag it out to pin it.

<details>
<summary>Run from source</summary>

You need Python 3.10 or newer on Windows.

```powershell
python -m pip install -r requirements.txt
python -m timetable
```

</details>

## Features

**Always visible, never in the way**
- **Click-through HUD** docked to the top or bottom of the screen. Clicks pass straight to the app underneath.
- **Stays on top** of other windows and is hidden from the taskbar. Works over normal and borderless-windowed apps; Windows doesn't allow overlays on exclusive-fullscreen games.
- **Follows your monitors**: plug in or unplug a screen, or change resolution, and the HUD moves and resizes itself. Pick its monitor in Settings.
- **Timeline view** with every interval sized by its length, plus a progress line and playhead.
- **Compact mode**: a thin line with small labels and a countdown on a clear background (opacity is adjustable).

**Sessions and tasks**
- **Sessions**: save named agendas ("Chemistry study", "Deep work"), each with its own colour.
- **To-do list per session**: the HUD shows your current task and a hotkey ticks it off.
- **Live editing**: change the agenda or tasks while the timer runs.

**Stats**
- **Stats window** (`Ctrl+Alt+S`) with Day, Week and Month views: a calendar, time per session, a 24-hour timeline, daily bars, top tasks and your streak.
- Everything stays on your computer.

![Stats window, month view](assets/screenshots/stats.png)

**Sound and alerts**
- **Ding** at the end of every interval and a three-note chime when the agenda finishes. Volume and a custom `.wav` are in Settings.
- **Warning pulse**: the countdown flashes amber in the last 30 seconds (configurable).

**Controls**
- **Global hotkeys** so you never need to click it, or switch on Interactive mode for on-screen buttons.

## Sessions, agendas and tasks

A **session** is a name, a colour, an agenda and a to-do list. Open **Sessions...** from the tray (or `Ctrl+Alt+E`) to
choose, create, duplicate, rename or delete one. Switching sessions restarts the timer and asks first if it is
part-way through. Everything you type is saved straight away.

![Sessions window](assets/screenshots/sessions.png)

**Agenda:** one interval per line, a name then a length: `50m`, `1h30m`, `45s`, or a bare number (minutes).
Names starting with Break, Rest, Lunch or Pause are drawn as breaks. Lines starting with `#` are ignored.
See [`examples/study-agenda.txt`](examples/study-agenda.txt).

**Tasks:** one per line. Start a line with `[x]` if it is done. The first unfinished task shows on the HUD, and
`Ctrl+Alt+Enter` ticks it and moves to the next. Time is credited to the task you were on when an interval began, which
feeds the Top tasks chart.

## Controls

Click-through means the HUD can't receive clicks, so use the tray or hotkeys. Turn on **Interactive mode** (tray menu or
`Ctrl+Alt+L`) to get a row of buttons on the HUD, then turn it off to go back to click-through.

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
| `Ctrl+Alt+S` | Stats window |

Tray icon: left-click starts or pauses, double-click toggles interactive mode, right-click opens the menu.
If another program already owns a hotkey, that one is skipped.

## Your data

Stored in `%APPDATA%\Timetable\`:

| File | Contents |
| --- | --- |
| `settings.json` | Appearance, sound and behaviour settings |
| `sessions.json` | Sessions: agendas, tasks and colours |
| `history.jsonl` | One line per finished, skipped or stopped interval: time, session, interval, planned and actual seconds, task, colour |

## Development

```powershell
pip install -r requirements.txt pytest ruff
python -m pytest
ruff check .
```

The timer logic (`engine.py`, `agenda.py`) and the stats maths (`stats.py`) have no GUI dependency and are unit tested.
See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## Ideas for later

Round clock style, a kanban board per session, a light theme, left/right docking, per-interval colours, seeking by clicking the timeline.

## License

[MIT](LICENSE)