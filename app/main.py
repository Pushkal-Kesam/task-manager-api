"""FastAPI application: HTTP layer only; business rules live in schemas/repository."""
import os
from functools import lru_cache
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status

from app.repository import TaskRepository
from app.schemas import Priority, Status, Task, TaskCreate, TaskUpdate

app = FastAPI(
    title="Task Manager API",
    version="1.0.0",
    description="A small, well-tested REST service for managing tasks.",
)


@lru_cache
def get_repository() -> TaskRepository:
    return TaskRepository(os.getenv("DB_PATH", "tasks.db"))


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate, repo: TaskRepository = Depends(get_repository)) -> Task:
    return repo.create(payload)


@app.get("/tasks", response_model=List[Task], tags=["tasks"])
def list_tasks(
    status_filter: Optional[Status] = Query(None, alias="status"),
    priority: Optional[Priority] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    repo: TaskRepository = Depends(get_repository),
) -> List[Task]:
    return repo.list(status_filter, priority, limit, offset)


@app.get("/tasks/{task_id}", response_model=Task, tags=["tasks"])
def get_task(task_id: int, repo: TaskRepository = Depends(get_repository)) -> Task:
    task = repo.get(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task, tags=["tasks"])
def update_task(
    task_id: int, payload: TaskUpdate, repo: TaskRepository = Depends(get_repository)
) -> Task:
    task = repo.update(task_id, payload)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: int, repo: TaskRepository = Depends(get_repository)) -> Response:
    if not repo.delete(task_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
