from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QTimer, Signal

STAGE_START = "start"
STAGE_EARLY = "early"
STAGE_DUE = "due"
STAGE_OVERDUE = "overdue"

NAG_INTERVAL = timedelta(minutes=10)


class ReminderService(QObject):
    reminder_due = Signal(object, str)

    def __init__(self, service, parent=None):
        super().__init__(parent)
        self._service = service
        self._last_nag: dict[int, datetime] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)
        self._timer.timeout.connect(self.check)
        self._timer.start()

    def start(self) -> None:
        self.check()

    def check(self) -> None:
        now = datetime.now()
        for task in self._service.start_reminders(now):
            self.reminder_due.emit(task, STAGE_START)
            self._service.mark_start_reminded(task.id)
        for task in self._service.due_reminders(now):
            if task.due_at is not None and now >= task.due_at - timedelta(seconds=60):
                stage = STAGE_DUE
            else:
                stage = STAGE_EARLY
            self.reminder_due.emit(task, stage)
            self._service.mark_reminded(task.id)
        overdue_ids = set()
        for task in self._service.overdue_tasks(now):
            overdue_ids.add(task.id)
            last = self._last_nag.get(task.id)
            if last is None or now - last >= NAG_INTERVAL:
                self._last_nag[task.id] = now
                self.reminder_due.emit(task, STAGE_OVERDUE)
        for task_id in list(self._last_nag):
            if task_id not in overdue_ids:
                del self._last_nag[task_id]
