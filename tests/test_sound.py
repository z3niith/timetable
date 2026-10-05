import array
import io
import wave

from timetable import sound


def test_scaled_wav_halves_volume(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("APPDATA", str(tmp_path))
    ding, done = sound.ensure_sounds()
    assert ding.exists() and done.exists()

    def peak(data: bytes) -> int:
        with wave.open(io.BytesIO(data)) as r:
            a = array.array("h")
            a.frombytes(r.readframes(r.getnframes()))
        return max(a)

    full = peak(sound._scaled_wav(ding, 1.0))
    half = peak(sound._scaled_wav(ding, 0.5))
    assert abs(half - full / 2) <= 1
