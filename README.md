# Task Manager API

[![CI](https://github.com/Pushkal-Kesam/task-manager-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Pushkal-Kesam/task-manager-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)

A small REST service for managing tasks, built with **FastAPI**, **Pydantic v2** and **SQLite**.
The goal is a compact codebase that still shows production habits: layered design, input validation,
isolated tests, enforced coverage, linting, containerisation and CI.

## Features

- Create, read, update (PATCH) and delete tasks
- Filter by `status` / `priority`, paginate with `limit` / `offset`
- Strict validation (blank or oversize titles, bad dates, unknown enums all return `422`)
- Interactive API docs generated at `/docs`

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/tasks` | Create a task (`201`) |
| GET | `/tasks` | List tasks, with `status`, `priority`, `limit`, `offset` |
| GET | `/tasks/{id}` | Fetch one task (`404` if missing) |
| PATCH | `/tasks/{id}` | Partial update |
| DELETE | `/tasks/{id}` | Delete (`204`) |

```bash
curl -X POST localhost:8000/tasks -H 'content-type: application/json' \
     -d '{"title": "Write release notes", "priority": "high", "due_date": "2030-01-31"}'

curl "localhost:8000/tasks?status=todo&priority=high"
```

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload          # http://localhost:8000/docs
```

With Docker:

```bash
docker build -t task-manager-api .
docker run -p 8000:8000 -v tasks-data:/data task-manager-api
```

## Test and lint

```bash
pytest          # 27 tests, fails the run if coverage drops below 90%
ruff check .
```

## Design notes

- **Layers:** `app/main.py` (HTTP) → `app/repository.py` (persistence) → `app/schemas.py` (contract).
  Routes contain no SQL; the repository contains no HTTP concepts.
- **Dependency injection:** the repository is injected with `Depends`, so tests swap in a fresh
  in-memory database per test. No shared state, no cleanup, no ordering bugs.
- **PATCH semantics:** `model_dump(exclude_unset=True)` distinguishes "field omitted" from
  "field set to null".
- **Container:** slim base image, non-root user, health check, data on a volume.
- **CI:** lint, tests on Python 3.9 and 3.12, then a Docker build.

## Possible next steps

Authentication, a Postgres repository behind the same interface, database migrations (Alembic).
