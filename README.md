# Timetable

An interval timer that floats over your screen, **always on top and click-through**, so you can see
where you are in a study or work session without it ever getting in the way.

## Features

- **Click-through HUD** docked to the top or bottom of the screen. Mouse clicks pass straight to the app underneath.
- **Always on top**, hidden from the taskbar. Lives in the system tray.
- **Timeline view**: every interval is a segment sized by its length, with a progress line and playhead.
- **Compact mode**: a thin line with small labels and a countdown, on a clear background by default (adjustable in Settings).
- **Ding** at the end of every interval, and a three-note chime when the whole agenda finishes. Volume and a custom `.wav` are in Settings.
- **Warning pulse**: the countdown flashes amber in the last 30 seconds (configurable).
- **Live agenda editing**: change the agenda while the timer runs.
- **Global hotkeys** so you never need to click it.

## Run it

**Winget (recommended):** use command `winget install z3niith.Timetable`.

**Installer (also recommended):** download `Timetable-Setup-<version>.exe` from the
[Releases page](https://github.com/z3niith/timetable/releases). It installs for your user only, with no admin prompt.

**From source:** you need Python 3.10 or newer on Windows.

```powershell
python -m pip install -r requirements.txt
python -m timetable
```

An icon appears in the system tray. On Windows 11 it may be tucked behind the `^` arrow; drag it out to pin it.

## Agenda format

One interval per line: a name, then a length. Lengths can be `50m`, `1h30m`, `45s`, or a bare number (minutes).
Names starting with Break, Rest, Lunch or Pause are drawn as breaks. Lines starting with `#` are ignored.
See [`examples/study-agenda.txt`](examples/study-agenda.txt).

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
| `Ctrl+Alt+E` | Edit agenda |

Tray icon: left-click toggles start/pause, double-click toggles interactive mode, right-click opens the menu.
If another program already owns a hotkey, that one is skipped.

Settings are saved to `%APPDATA%\Timetable\settings.json`.

## Development

```powershell
pip install -r requirements.txt pytest
python -m pytest
```

The timer logic (`engine.py`, `agenda.py`) has no GUI dependency and is unit tested.

## Ideas for later

Left/right docking, multi-monitor choice, per-interval colors, saved agenda presets, seeking by clicking the timeline.

## License

MIT
