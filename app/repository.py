"""Persistence layer (SQLite). Isolated so it can be unit-tested and swapped."""
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.schemas import Priority, Status, Task, TaskCreate, TaskUpdate

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'todo',
    priority    TEXT NOT NULL DEFAULT 'medium',
    due_date    TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskRepository:
    def __init__(self, db_path: str = "tasks.db"):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(SCHEMA)
        self._conn.commit()

    @staticmethod
    def _to_task(row: sqlite3.Row) -> Task:
        return Task(**dict(row))

    def create(self, data: TaskCreate) -> Task:
        now = _now()
        cursor = self._conn.execute(
            "INSERT INTO tasks (title, description, status, priority, due_date, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data.title,
                data.description,
                Status.todo.value,
                data.priority.value,
                data.due_date.isoformat() if data.due_date else None,
                now,
                now,
            ),
        )
        self._conn.commit()
        return self.get(cursor.lastrowid)  # type: ignore[return-value]

    def get(self, task_id: int) -> Optional[Task]:
        row = self._conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._to_task(row) if row else None

    def list(
        self,
        status: Optional[Status] = None,
        priority: Optional[Priority] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Task]:
        clauses, params = [], []
        if status:
            clauses.append("status = ?")
            params.append(status.value)
        if priority:
            clauses.append("priority = ?")
            params.append(priority.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._conn.execute(
            f"SELECT * FROM tasks {where} ORDER BY id LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
        return [self._to_task(r) for r in rows]

    def update(self, task_id: int, data: TaskUpdate) -> Optional[Task]:
        changes: Dict[str, object] = data.model_dump(exclude_unset=True)
        if not changes:
            return self.get(task_id)
        if "due_date" in changes and changes["due_date"] is not None:
            changes["due_date"] = changes["due_date"].isoformat()
        for key in ("status", "priority"):
            if key in changes and changes[key] is not None:
                changes[key] = changes[key].value
        changes["updated_at"] = _now()
        assignments = ", ".join(f"{column} = ?" for column in changes)
        cursor = self._conn.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?", (*changes.values(), task_id)
        )
        self._conn.commit()
        return self.get(task_id) if cursor.rowcount else None

    def delete(self, task_id: int) -> bool:
        cursor = self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()
        return cursor.rowcount > 0
