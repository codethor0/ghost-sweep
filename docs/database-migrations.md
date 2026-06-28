# Database Migrations

ghost-sweep uses Alembic with async SQLAlchemy against PostgreSQL 15. Batch 2 introduces the initial UUID schema migration that matches the current ORM models.

## Prerequisites

- Python 3.11
- PostgreSQL 15
- Backend dev dependencies installed: `pip install "./backend[dev]"`
- A dedicated database for local development or testing

## Environment variables

| Variable | Purpose |
| -------- | ------- |
| `DATABASE_URL` | Application database URL used by FastAPI and Alembic at runtime |
| `TEST_DATABASE_URL` | Integration test database URL used by pytest migration and DB fixtures |

Example test URL when using Docker Compose `postgres_test` on the host:

```text
postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5433/ghost_sweep_test
```

The main development database on port 5432 uses database name `ghost_sweep`, not `ghost_sweep_test`.

## Apply migrations locally

From the repository root:

```bash
cd backend
alembic upgrade head
```

Alembic reads `DATABASE_URL` through `app.config.get_settings()`.

## Verify migrations in tests

Migration verification tests require `TEST_DATABASE_URL`:

```bash
cd backend
TEST_DATABASE_URL="postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5432/ghost_sweep_test" \
  pytest tests/test_migrations.py -v
```

These tests verify:

- Alembic records revision `001_initial_uuid_schema`
- Core entity tables exist
- Native PostgreSQL ENUM types exist
- `uq_votes_report_user` is present on `votes`
- Downgrade to base and upgrade to head succeed

Unit tests that do not require PostgreSQL continue to run without `TEST_DATABASE_URL`.

## Schema strategy

- Primary keys use UUID columns
- Enumerated model fields use PostgreSQL native ENUM types
- JSONB stores list and breakdown payloads
- Foreign keys follow the current ORM relationship graph
- `votes.report_id` and `votes.user_id` are unique together

## Rollback

To remove the initial schema locally:

```bash
cd backend
alembic downgrade base
```

Downgrade drops all Batch 1 tables and removes the PostgreSQL ENUM types created by the initial migration.

## Out of scope for Batch 2

- Docker entrypoint migration automation
- CI migration steps
- API routes and auth flows
- Frontend, extension, and deployment changes

Those items are planned for later batches after the database foundation is reviewed.
