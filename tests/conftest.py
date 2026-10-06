import pytest
from fastapi.testclient import TestClient

from app.main import app, get_repository
from app.repository import TaskRepository


@pytest.fixture()
def repo() -> TaskRepository:
    """Fresh in-memory database for every test: no shared state, no cleanup."""
    return TaskRepository(":memory:")


@pytest.fixture()
def client(repo: TaskRepository):
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
