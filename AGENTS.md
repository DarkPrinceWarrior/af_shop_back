# Repository Guidelines

## Project Structure & Module Organization

This repository is the Shop Meraj FastAPI backend.

- `app/main.py` configures the FastAPI app, CORS, media serving, and API router.
- `app/api/routes/` contains route modules: catalog, admin, auth, users, and utils.
- `app/models.py` contains SQLModel database models and API schemas.
- `app/services/` contains business logic for orders, Telegram, and realtime events.
- `app/alembic/versions/` contains database migrations.
- `tests/` contains pytest coverage for API routes, CRUD, and startup scripts.
- `docs/` contains API and seed-data documentation.
- `seed/` contains JSON seed templates for catalog data.

## Build, Test, and Development Commands

Install dependencies:

```bash
uv sync
```

Run locally without Docker:

```bash
uv run fastapi dev
```

Run with Docker:

```bash
docker compose up --build -d
```

Validate production compose:

```bash
docker compose -f compose.prod.yaml config --quiet
```

Run checks:

```bash
uv run pytest
uv run ruff check app tests
python3 -m compileall -q app tests
```

## Coding Style & Naming Conventions

Use Python 3.10+ style with type hints. Prefer small route handlers and move business logic into `app/services/`. Use `snake_case` for functions, variables, and modules; use `PascalCase` for models and schemas. Keep FastAPI dependencies in `Annotated[...]` style where possible. Ruff is the source of truth for linting.

## Testing Guidelines

Tests use `pytest` and `fastapi.testclient.TestClient`. Place API tests in `tests/api/routes/` and name files `test_*.py`. Add tests for new order, catalog, admin, seed, and migration-sensitive behavior. Mock external services such as Telegram; tests must not send real notifications.

## Commit & Pull Request Guidelines

Commit history uses short imperative messages, for example `Add admin order filters` or `Add JSON shop seed import`. Keep commits scoped to one change. Pull requests should include a short summary, test results, migration notes if applicable, and screenshots or API examples for user-facing changes.

## Repository Workflow & Tools

Use `fff` first for file search and code grep in this repository. If `fff` cannot express the query or is unavailable, fall back to shell tools. After locating the relevant area, use Serena for symbolic navigation and edits: `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`, and symbol-level edit tools when appropriate.

Use the FastAPI skill when changing routes, dependencies, schemas, Pydantic models, startup logic, or API behavior. Use Context7 for version-sensitive framework or library details. Use Tavily only for fresh external research or documentation lookup.

Before editing, inspect current code and state what will change. Prefer minimal, localized edits. Do not rename files, move modules, install dependencies, alter public APIs, or edit secrets unless the task requires it. Never revert user changes or run destructive git commands without explicit approval.

## Security & Configuration Tips

Never commit `.env`, tokens, passwords, database dumps, or uploaded media. Use `.env.example` for placeholders only. For production, replace default secrets and run with `compose.prod.yaml`. Use `docs/seed_data.md` for catalog imports instead of hardcoding real shop data in Python.
