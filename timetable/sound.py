"""Ding sounds. Generated on first run so the repo needs no audio assets."""

from __future__ import annotations

import array
import io
import math
import struct
import sys
import wave
import zlib
from pathlib import Path

from .settings import Settings, config_dir

RATE = 44100


def _tone(freq: float, seconds: float, decay: float = 4.5) -> list[float]:
    n = int(RATE * seconds)
    out = []
    for i in range(n):
        t = i / RATE
        env = math.exp(-decay * t) * min(1.0, t / 0.004)  # 4 ms attack avoids a click
        v = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2.01 * t)
        out.append(0.5 * env * v)
    return out


def _write(path: Path, samples: list[float]) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32767)) for s in samples))


def ensure_sounds() -> tuple[Path, Path]:
    folder = config_dir()
    ding, done = folder / "ding.wav", folder / "done.wav"
    if not ding.exists():
        _write(ding, _tone(988, 1.4))
    if not done.exists():
        mix = [0.0] * int(RATE * 2.2)
        for k, f in enumerate((784, 988, 1319)):
            for i, v in enumerate(_tone(f, 1.4)):
                j = i + int(RATE * 0.22 * k)
                if j < len(mix):
                    mix[j] += v
        _write(done, mix)
    return ding, done


def _scaled_wav(path: Path, volume: float) -> bytes:
    """Read a 16-bit PCM wav and return it as bytes with the volume applied."""
    with wave.open(str(path), "rb") as r:
        params, frames = r.getparams(), r.readframes(r.getnframes())
    if params.sampwidth == 2:
        samples = array.array("h")
        samples.frombytes(frames)
        if sys.byteorder == "big":
            samples.byteswap()
        samples = array.array("h", (int(v * volume) for v in samples))
        if sys.byteorder == "big":
            samples.byteswap()
        frames = samples.tobytes()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setparams(params)
        w.writeframes(frames)
    return buf.getvalue()


class SoundPlayer:
    """Plays dings with the standard library on Windows (no extra packages needed).
    On other systems it uses Qt Multimedia if installed, otherwise stays silent."""

    def __init__(self, settings: Settings):
        self.s = settings
        self._paths: dict[str, Path] = {}
        self._qt = {}
        self.reload()

    def reload(self) -> None:
        ding, done = ensure_sounds()
        custom = Path(self.s.sound_file) if self.s.sound_file else None
        if custom and custom.is_file():
            ding = custom
        self._paths = {"ding": ding, "done": done}

    def _prepared(self, which: str, volume: float) -> Path:
        """Path of a copy of the sound with the volume applied, created on first use."""
        src = self._paths[which]
        tag = zlib.crc32(f"{src}|{src.stat().st_mtime_ns}".encode()) & 0xFFFFFF
        folder = config_dir() / "cache"
        folder.mkdir(exist_ok=True)
        out = folder / f"{which}-{round(volume * 100)}-{tag:06x}.wav"
        if not out.exists():
            out.write_bytes(_scaled_wav(src, volume))
        return out

    def play(self, which: str = "ding", force: bool = False) -> None:
        if (not self.s.ding_enabled and not force) or which not in self._paths:
            return
        volume = max(0.0, min(1.0, self.s.volume))
        if sys.platform == "win32":
            import winsound

            try:
                # winsound can't play from memory asynchronously, so play a volume-scaled file.
                winsound.PlaySound(str(self._prepared(which, volume)), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except (OSError, RuntimeError, wave.Error):
                pass  # a sound problem must never break the timer
            return
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QSoundEffect
        except ImportError:
            return
        eff = self._qt.setdefault(which, QSoundEffect())
        eff.setSource(QUrl.fromLocalFile(str(self._paths[which])))
        eff.setVolume(volume)
        eff.play()
