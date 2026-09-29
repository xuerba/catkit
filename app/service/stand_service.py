import ctypes

from PySide6.QtCore import QObject, QTimer, Signal

from app.settings import AppSettings

POLL_MS = 10_000
AWAY_IDLE_LIMIT = 300.0


def idle_seconds() -> float:
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_uint),
                ("dwTime", ctypes.c_uint),
            ]

        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if user32.GetLastInputInfo(ctypes.byref(info)):
            return (kernel32.GetTickCount() - info.dwTime) / 1000.0
    except AttributeError:
        pass
    return 0.0


class StandService(QObject):
    stand_due = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = AppSettings.stand_reminder_enabled()
        self._interval = AppSettings.stand_interval()
        self._accumulated = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_MS)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def interval(self) -> int:
        return self._interval

    def set_enabled(self, value: bool):
        self._enabled = bool(value)
        AppSettings.set_stand_reminder_enabled(self._enabled)
        if not self._enabled:
            self._accumulated = 0.0

    def set_interval(self, minutes: int):
        self._interval = int(minutes)
        AppSettings.set_stand_interval(self._interval)

    def _on_tick(self):
        if not self._enabled:
            return
        idle = idle_seconds()
        if idle >= AWAY_IDLE_LIMIT:
            self._accumulated = 0.0
            return
        self._accumulated += POLL_MS / 1000.0
        if self._accumulated >= self._interval * 60:
            self._accumulated = 0.0
            self.stand_due.emit(self._interval)
