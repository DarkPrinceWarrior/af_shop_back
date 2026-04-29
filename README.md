# Shop Meraj Backend

FastAPI backend scaffold based on `fastapi/full-stack-fastapi-template` (`master` branch).

## Stack

- FastAPI
- Pydantic v2 and pydantic-settings
- SQLModel
- PostgreSQL via psycopg
- Alembic migrations
- Pytest, Ruff, mypy, ty
- uv for dependency and virtualenv management

## Local Development

Install dependencies from this directory:

```bash
uv sync
```

Create a local environment file:

```bash
cp .env.example .env
```

Run the development server:

```bash
uv run fastapi dev
```

The FastAPI entrypoint is configured in `pyproject.toml` as `app.main:app`.

## Tests

```bash
uv run pytest
```

The copied template also includes `scripts/test.sh` and Docker support if we decide to keep that workflow later.

## Docker

From this directory:

```bash
docker compose up --build
```

The API will be available at:

- `http://localhost:8000`
- `http://localhost:8000/docs`

The compose stack starts PostgreSQL and runs Alembic migrations before starting FastAPI.

## Structure

- `app/main.py` - FastAPI application setup
- `app/api/` - API router and route modules
- `app/core/` - settings, database, security
- `app/services/` - order, real-time, and Telegram services
- `app/models.py` - SQLModel models and Pydantic schemas
- `app/crud.py` - CRUD helpers
- `app/alembic/` - migrations
- `tests/` - pytest suite
