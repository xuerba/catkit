import math
import os
import struct
import wave
from pathlib import Path

from app.db import DB_DIR


RATE = 44100


def _generate_meow(path: Path) -> None:
    rate = RATE
    duration = 0.45
    total = int(rate * duration)
    frames = []
    for i in range(total):
        t = i / rate
        progress = t / duration
        freq = 620.0 - 260.0 * progress
        wobble = 1.0 + 0.04 * math.sin(2 * math.pi * 22 * t)
        if progress < 0.18:
            amp = math.sin(math.pi * progress / 0.18)
        else:
            amp = (1.0 - progress) ** 1.5
        value = 0.45 * amp * math.sin(2 * math.pi * freq * wobble * t)
        value += 0.12 * amp * math.sin(2 * math.pi * freq * 2 * wobble * t)
        frames.append(struct.pack("<h", int(value * 32000)))
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(b"".join(frames))


class MeowPlayer:
    def __init__(self):
        self._effect = None
        self.muted = False
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QSoundEffect

            path = DB_DIR / "meow.wav"
            regenerate = True
            if path.exists():
                try:
                    with wave.open(str(path), "rb") as f:
                        regenerate = f.getframerate() != RATE
                except Exception:
                    regenerate = True
            if regenerate:
                _generate_meow(path)
            if os.environ.get("QT_QPA_PLATFORM", "") == "offscreen":
                self._effect = None
            else:
                effect = QSoundEffect()
                effect.setSource(QUrl.fromLocalFile(str(path)))
                effect.setVolume(0.25)
                self._effect = effect
        except Exception:
            self._effect = None

    def play(self) -> None:
        if self._effect is None or self.muted:
            return
        try:
            from PySide6.QtMultimedia import QSoundEffect

            if self._effect.status() == QSoundEffect.Error:
                self._effect = None
                return
            self._effect.play()
        except Exception:
            self._effect = None

    def set_muted(self, muted: bool) -> None:
        self.muted = bool(muted)
