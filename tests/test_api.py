import pytest


def make_task(client, **overrides):
    payload = {"title": "Write tests", "priority": "high", **overrides}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_fetch_task(client):
    created = make_task(client, description="cover the happy path", due_date="2030-05-01")
    assert created["status"] == "todo"
    assert created["priority"] == "high"
    fetched = client.get(f"/tasks/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created


def test_title_is_trimmed(client):
    assert make_task(client, title="  padded  ")["title"] == "padded"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 101},
        {"title": "ok", "priority": "urgent"},
        {"title": "ok", "due_date": "not-a-date"},
    ],
)
def test_create_rejects_invalid_payload(client, payload):
    assert client.post("/tasks", json=payload).status_code == 422


def test_list_supports_filters_and_pagination(client):
    for i in range(4):
        make_task(client, title=f"task {i}", priority="low" if i < 2 else "high")
    client.patch("/tasks/1", json={"status": "done"})

    assert len(client.get("/tasks").json()) == 4
    assert [t["id"] for t in client.get("/tasks", params={"status": "done"}).json()] == [1]
    assert len(client.get("/tasks", params={"priority": "high"}).json()) == 2
    assert [t["id"] for t in client.get("/tasks", params={"limit": 2, "offset": 1}).json()] == [2, 3]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 500}, {"offset": -1}, {"status": "nope"}])
def test_list_rejects_bad_query_params(client, params):
    assert client.get("/tasks", params=params).status_code == 422


def test_patch_updates_only_given_fields(client):
    task = make_task(client)
    response = client.patch(f"/tasks/{task['id']}", json={"status": "in_progress"})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "in_progress"
    assert body["title"] == task["title"]


def test_patch_rejects_blank_title(client):
    task = make_task(client)
    assert client.patch(f"/tasks/{task['id']}", json={"title": " "}).status_code == 422


def test_delete_then_404(client):
    task = make_task(client)
    assert client.delete(f"/tasks/{task['id']}").status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_task_returns_404(client, method):
    kwargs = {"json": {"title": "x"}} if method == "patch" else {}
    assert getattr(client, method)("/tasks/999", **kwargs).status_code == 404
