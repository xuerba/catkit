from datetime import datetime

from app.db import connect
from app.model.task import (
    STATUS_DOING,
    STATUS_DONE,
    STATUS_TODO,
    Task,
)


def _dt(value):
    return datetime.fromisoformat(value) if value else None


def _iso(value):
    return value.isoformat() if value else None


def _to_task(row) -> Task:
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        category=row["category"],
        dri=row["dri"],
        start_at=_dt(row["start_at"]),
        due_at=_dt(row["due_at"]),
        priority=row["priority"],
        status=row["status"],
        remind_at=_dt(row["remind_at"]),
        reminded=bool(row["reminded"]),
        start_remind_at=_dt(row["start_remind_at"]),
        start_reminded=bool(row["start_reminded"]),
        created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]),
    )


class TaskRepository:
    def __init__(self, conn=None):
        self._conn = conn or connect()

    def list_tasks(self, keyword: str = "", status_filter: str = "all") -> list[Task]:
        sql = "SELECT * FROM tasks"
        conds = []
        params: list = []
        if keyword:
            conds.append(
                "(title LIKE ? OR description LIKE ? OR category LIKE ? OR dri LIKE ?)"
            )
            params += [f"%{keyword}%"] * 4
        if status_filter == "overdue":
            conds.append("status != 'done' AND due_at IS NOT NULL AND due_at < ?")
            params.append(datetime.now().isoformat())
        elif status_filter in (STATUS_TODO, STATUS_DOING, STATUS_DONE):
            conds.append("status = ?")
            params.append(status_filter)
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += (
            " ORDER BY CASE WHEN due_at IS NULL THEN 1 ELSE 0 END, "
            "due_at, priority DESC, id DESC"
        )
        return [_to_task(r) for r in self._conn.execute(sql, params)]

    def get(self, task_id: int) -> Task | None:
        row = self._conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return _to_task(row) if row else None

    def add(self, task: Task) -> Task:
        cur = self._conn.execute(
            "INSERT INTO tasks (title, description, category, dri, start_at,"
            " due_at, priority, status, remind_at, reminded, start_remind_at,"
            " start_reminded, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.title,
                task.description,
                task.category,
                task.dri,
                _iso(task.start_at),
                _iso(task.due_at),
                task.priority,
                task.status,
                _iso(task.remind_at),
                int(task.reminded),
                _iso(task.start_remind_at),
                int(task.start_reminded),
                _iso(task.created_at),
                _iso(task.updated_at),
            ),
        )
        self._conn.commit()
        task.id = cur.lastrowid
        return task

    def update(self, task: Task) -> None:
        self._conn.execute(
            "UPDATE tasks SET title=?, description=?, category=?, dri=?, start_at=?,"
            " due_at=?, priority=?, status=?, remind_at=?, reminded=?,"
            " start_remind_at=?, start_reminded=?, updated_at=? WHERE id=?",
            (
                task.title,
                task.description,
                task.category,
                task.dri,
                _iso(task.start_at),
                _iso(task.due_at),
                task.priority,
                task.status,
                _iso(task.remind_at),
                int(task.reminded),
                _iso(task.start_remind_at),
                int(task.start_reminded),
                _iso(task.updated_at),
                task.id,
            ),
        )
        self._conn.commit()

    def delete(self, task_id: int) -> None:
        self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()

    def due_reminders(self, now: datetime) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE remind_at IS NOT NULL AND reminded = 0"
            " AND status != 'done' AND remind_at <= ? ORDER BY remind_at",
            (now.isoformat(),),
        )
        return [_to_task(r) for r in rows]

    def start_reminders(self, now: datetime) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE start_remind_at IS NOT NULL"
            " AND start_reminded = 0 AND status != 'done'"
            " AND start_remind_at <= ? ORDER BY start_remind_at",
            (now.isoformat(),),
        )
        return [_to_task(r) for r in rows]

    def overdue(self, now: datetime) -> list[Task]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE status != 'done' AND due_at IS NOT NULL"
            " AND due_at < ? ORDER BY due_at",
            (now.isoformat(),),
        )
        return [_to_task(r) for r in rows]

    def mark_reminded(self, task_id: int) -> None:
        self._conn.execute(
            "UPDATE tasks SET reminded = 1 WHERE id = ?", (task_id,)
        )
        self._conn.commit()

    def mark_start_reminded(self, task_id: int) -> None:
        self._conn.execute(
            "UPDATE tasks SET start_reminded = 1 WHERE id = ?", (task_id,)
        )
        self._conn.commit()

    def stats(self, now: datetime) -> dict:
        counts = {STATUS_TODO: 0, STATUS_DOING: 0, STATUS_DONE: 0}
        for row in self._conn.execute(
            "SELECT status, COUNT(*) AS c FROM tasks GROUP BY status"
        ):
            if row["status"] in counts:
                counts[row["status"]] = row["c"]
        overdue = self._conn.execute(
            "SELECT COUNT(*) AS c FROM tasks WHERE status != 'done'"
            " AND due_at IS NOT NULL AND due_at < ?",
            (now.isoformat(),),
        ).fetchone()["c"]
        counts["overdue"] = overdue
        return counts
