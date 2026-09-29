from PySide6.QtCore import QObject, QTimer, Signal

from app.ui import sprite

FRAME_MS = 150


class Animator(QObject):
    frame_ready = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._frames: list = []
        self._index = 0
        self._loop = True
        self._on_done = None
        self._size = sprite.SIZE
        self._timer = QTimer(self)
        self._timer.setInterval(FRAME_MS)
        self._timer.timeout.connect(self._next_frame)

    def set_size(self, size: int):
        self._size = int(size)

    def set_state(self, state: str, loop: bool = True, on_done=None, fps: float | None = None):
        self._frames = sprite.build_frames(state, self._size)
        self._index = 0
        self._loop = loop
        self._on_done = on_done
        if fps:
            self._timer.setInterval(int(1000 / fps))
        else:
            self._timer.setInterval(FRAME_MS)
        if self._frames:
            self.frame_ready.emit(self._frames[0])
        self._timer.start()

    def stop(self):
        self._timer.stop()

    def _next_frame(self):
        if not self._frames:
            return
        self._index += 1
        if self._index >= len(self._frames):
            if self._loop:
                self._index = 0
            else:
                self._timer.stop()
                self._index = len(self._frames) - 1
                callback = self._on_done
                self._on_done = None
                if callback:
                    callback()
                    return
        self.frame_ready.emit(self._frames[self._index])
