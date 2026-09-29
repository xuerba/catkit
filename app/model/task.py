from dataclasses import dataclass
from datetime import datetime

STATUS_TODO = "todo"
STATUS_DOING = "doing"
STATUS_DONE = "done"

STATUS_NAMES = {
    STATUS_TODO: "待開始",
    STATUS_DOING: "進行中",
    STATUS_DONE: "已完成",
}

PRIORITY_NAMES = {0: "低", 1: "中", 2: "高"}


@dataclass
class Task:
    id: int | None = None
    title: str = ""
    description: str = ""
    category: str = ""
    dri: str = ""
    start_at: datetime | None = None
    due_at: datetime | None = None
    priority: int = 1
    status: str = STATUS_TODO
    remind_at: datetime | None = None
    reminded: bool = False
    start_remind_at: datetime | None = None
    start_reminded: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_overdue(self, now: datetime) -> bool:
        return self.status != STATUS_DONE and self.due_at is not None and self.due_at < now
