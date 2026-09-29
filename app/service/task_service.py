from datetime import datetime, timedelta

from app.model.repository import TaskRepository
from app.model.task import (
    STATUS_DOING,
    STATUS_DONE,
    STATUS_TODO,
    Task,
)

_STATUS_CYCLE = {STATUS_TODO: STATUS_DOING, STATUS_DOING: STATUS_DONE, STATUS_DONE: STATUS_TODO}


class TaskService:
    def __init__(self, repo: TaskRepository | None = None):
        self.repo = repo or TaskRepository()

    def create(
        self,
        title: str,
        description: str = "",
        category: str = "",
        dri: str = "",
        start_at=None,
        due_at=None,
        priority: int = 1,
        remind_at=None,
        start_remind_at=None,
    ) -> Task:
        title = (title or "").strip()
        if not title:
            raise ValueError("任務標題不可為空")
        now = datetime.now()
        task = Task(
            title=title,
            description=description or "",
            category=(category or "").strip(),
            dri=(dri or "").strip(),
            start_at=start_at,
            due_at=due_at,
            priority=int(priority),
            status=STATUS_TODO,
            remind_at=remind_at,
            start_remind_at=start_remind_at,
            created_at=now,
            updated_at=now,
        )
        return self.repo.add(task)

    def update(
        self,
        task_id: int,
        title: str,
        description: str,
        category: str,
        dri: str,
        start_at,
        due_at,
        priority: int,
        remind_at,
        start_remind_at=None,
    ) -> Task:
        task = self.get(task_id)
        if task is None:
            raise ValueError("任務不存在")
        title = (title or "").strip()
        if not title:
            raise ValueError("任務標題不可為空")
        if task.remind_at != remind_at:
            task.reminded = False
        if task.start_remind_at != start_remind_at:
            task.start_reminded = False
        task.title = title
        task.description = description or ""
        task.category = (category or "").strip()
        task.dri = (dri or "").strip()
        task.start_at = start_at
        task.due_at = due_at
        task.priority = int(priority)
        task.remind_at = remind_at
        task.start_remind_at = start_remind_at
        task.updated_at = datetime.now()
        self.repo.update(task)
        return task

    def get(self, task_id: int) -> Task | None:
        return self.repo.get(task_id)

    def list_tasks(self, keyword: str = "", status_filter: str = "all") -> list[Task]:
        return self.repo.list_tasks(keyword, status_filter)

    def delete(self, task_id: int) -> None:
        self.repo.delete(task_id)

    def cycle_status(self, task_id: int) -> Task:
        task = self.get(task_id)
        if task is None:
            raise ValueError("任務不存在")
        task.status = _STATUS_CYCLE[task.status]
        task.updated_at = datetime.now()
        self.repo.update(task)
        return task

    def set_status(self, task_id: int, status: str) -> Task:
        task = self.get(task_id)
        if task is None:
            raise ValueError("任務不存在")
        task.status = status
        task.updated_at = datetime.now()
        self.repo.update(task)
        return task

    def snooze(self, task_id: int, minutes: int) -> Task:
        task = self.get(task_id)
        if task is None:
            raise ValueError("任務不存在")
        task.remind_at = datetime.now() + timedelta(minutes=minutes)
        task.reminded = False
        task.updated_at = datetime.now()
        self.repo.update(task)
        return task

    def due_reminders(self, now: datetime) -> list[Task]:
        return self.repo.due_reminders(now)

    def start_reminders(self, now: datetime) -> list[Task]:
        return self.repo.start_reminders(now)

    def overdue_tasks(self, now: datetime) -> list[Task]:
        return self.repo.overdue(now)

    def mark_reminded(self, task_id: int) -> None:
        self.repo.mark_reminded(task_id)

    def mark_start_reminded(self, task_id: int) -> None:
        self.repo.mark_start_reminded(task_id)

    def stats(self, now: datetime | None = None) -> dict:
        return self.repo.stats(now or datetime.now())
