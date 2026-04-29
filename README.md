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

## Environment

Create a local environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Set real values in `.env` before production use:

- `SECRET_KEY`
- `FIRST_SUPERUSER`
- `FIRST_SUPERUSER_PASSWORD`
- `POSTGRES_PASSWORD`
- `FRONTEND_HOST`
- `BACKEND_CORS_ORIGINS`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_OWNER_CHAT_ID`

Do not commit `.env`.

## Local Development

Install dependencies from this directory:

```bash
uv sync
```

Run the development server without Docker:

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

Detached mode:

```bash
docker compose up --build -d
```

The API will be available at:

- `http://localhost:8000`
- `http://localhost:8000/docs`
- `http://localhost:8000/api/v1/utils/health-check/`

The compose stack starts PostgreSQL and runs Alembic migrations before starting FastAPI.
On startup it also creates demo seed data when the shop tables are empty:

- 3 categories
- 4 products with stock and prices in AFN, CNY, and USD
- 10 delivery places with delivery fees

Custom catalog seed data can be loaded from `seed/shop_seed.json`.
See `docs/seed_data.md`.

Check containers:

```bash
docker compose ps
docker compose logs backend
```

## Production Compose

Use `compose.prod.yaml` when deploying to a server:

```bash
docker compose -f compose.prod.yaml up --build -d
```

Production compose:

- requires secrets from `.env`;
- does not expose PostgreSQL to the host;
- exposes the backend on `${BACKEND_PORT:-8000}`;
- runs migrations before FastAPI starts;
- uses Docker healthchecks for Postgres and backend.

Production compose forces `ENVIRONMENT=production`; replace all placeholder secrets in `.env` before starting it.

## Telegram Check

After setting `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_CHAT_ID`, create a test order through Swagger:

1. Open `http://localhost:8000/docs`.
2. Use `POST /api/v1/catalog/orders`.
3. Submit a valid product id and delivery place id from `GET /api/v1/catalog/bootstrap`.
4. Confirm that a new order message arrives in Telegram.

## Backup and Restore

Create a backup directory:

```bash
mkdir -p backups
```

Backup Postgres from the local Docker stack:

```bash
docker compose exec db pg_dump -U postgres -d shop_meraj -Fc -f /tmp/shop_meraj.dump
docker compose cp db:/tmp/shop_meraj.dump ./backups/shop_meraj.dump
```

Restore into the local Docker stack:

```bash
docker compose cp ./backups/shop_meraj.dump db:/tmp/shop_meraj.dump
docker compose exec db pg_restore -U postgres -d shop_meraj --clean --if-exists /tmp/shop_meraj.dump
```

If you change `POSTGRES_USER` or `POSTGRES_DB`, replace `postgres` and `shop_meraj` in those commands.

## Structure

- `app/main.py` - FastAPI application setup
- `app/api/` - API router and route modules
- `app/core/` - settings, database, security
- `app/services/` - order, real-time, and Telegram services
- `app/models.py` - SQLModel models and Pydantic schemas
- `app/crud.py` - CRUD helpers
- `app/alembic/` - migrations
- `tests/` - pytest suite
