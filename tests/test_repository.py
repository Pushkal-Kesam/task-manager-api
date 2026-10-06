from datetime import date

from app.schemas import Priority, Status, TaskCreate, TaskUpdate


def test_create_applies_defaults(repo):
    task = repo.create(TaskCreate(title="Write docs"))
    assert task.id == 1
    assert task.status == Status.todo
    assert task.priority == Priority.medium
    assert task.created_at == task.updated_at


def test_get_missing_returns_none(repo):
    assert repo.get(42) is None


def test_list_filters_and_paginates(repo):
    for i in range(5):
        repo.create(TaskCreate(title=f"t{i}", priority=Priority.high if i % 2 else Priority.low))
    repo.update(1, TaskUpdate(status=Status.done))

    assert len(repo.list()) == 5
    assert [t.id for t in repo.list(status=Status.done)] == [1]
    assert {t.priority for t in repo.list(priority=Priority.high)} == {Priority.high}
    assert [t.id for t in repo.list(limit=2, offset=2)] == [3, 4]


def test_update_is_partial_and_stores_due_date(repo):
    task = repo.create(TaskCreate(title="Ship", description="keep me"))
    updated = repo.update(task.id, TaskUpdate(due_date=date(2030, 1, 31), status=Status.in_progress))
    assert updated.title == "Ship"
    assert updated.description == "keep me"
    assert updated.due_date == date(2030, 1, 31)
    assert updated.status == Status.in_progress


def test_update_with_no_changes_returns_task(repo):
    task = repo.create(TaskCreate(title="Same"))
    assert repo.update(task.id, TaskUpdate()) == task


def test_update_and_delete_missing(repo):
    assert repo.update(99, TaskUpdate(title="x")) is None
    assert repo.delete(99) is False


def test_delete_removes_task(repo):
    task = repo.create(TaskCreate(title="Temp"))
    assert repo.delete(task.id) is True
    assert repo.get(task.id) is None
