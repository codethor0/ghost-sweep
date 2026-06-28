# Local Docker Validation Checkpoint

This document records the first live-validated milestone for ghost-sweep after Batch 4 (commit `6a0e6c0`) was pushed to the private GitHub repository.

## Validated Docker services

The following services were started with `docker compose` and reported healthy:

| Service | Host port | Status |
| ------- | --------- | ------ |
| `postgres` | 5432 | Healthy |
| `postgres_test` | 5433 | Healthy |
| `redis` | 6379 | Healthy |
| `backend` | 8000 | Running after migration resolution |
| `frontend` | 3000 | Running |

Infrastructure-only startup:

```bash
docker compose up -d postgres redis
docker compose ps
```

Full stack startup:

```bash
docker compose up -d backend frontend
docker compose ps
docker compose logs --tail=200 backend
```

## Backend URLs tested

| URL | Expected result |
| --- | --------------- |
| `http://localhost:8000/` | HTTP 200, service metadata JSON |
| `http://localhost:8000/health` | HTTP 200, basic service health JSON |

Example:

```bash
curl -i http://localhost:8000/
curl -i http://localhost:8000/health
```

## Auth endpoints tested

The following auth lifecycle was validated live against the Docker backend with Redis available:

| Endpoint | Result |
| -------- | ------ |
| `POST /api/v1/auth/register` | HTTP 200, access and refresh tokens returned |
| `POST /api/v1/auth/login` | HTTP 200 |
| `GET /api/v1/auth/me` | HTTP 200 with bearer access token |
| `POST /api/v1/auth/refresh` | HTTP 200, new access token returned |
| `POST /api/v1/auth/logout` | HTTP 204 No Content |
| `POST /api/v1/auth/refresh` after logout | HTTP 401 |

Refresh tokens are opaque, stored in Redis by SHA-256 hash, and revoked on logout. Access tokens remain valid until JWT expiration after logout.

See [auth-api.md](auth-api.md) for request and response details.

## Frontend status

The frontend container serves at `http://localhost:3000` and returns the Next.js app shell with title `ghost-sweep`.

The frontend is scaffold only. It is not wired to the current auth API or domain endpoints.

## Extension status

The browser extension exists in the repository under `extension/` for Chrome and Firefox Manifest V3.

The extension was not live-tested against the current API during this checkpoint. Extension integration remains deferred.

## Existing local Postgres: empty alembic_version

During live validation, the Docker Postgres development database already contained application tables, but the `alembic_version` table was empty. In that state, `alembic upgrade head` fails with errors such as:

```text
DuplicateTableError: relation "companies" already exists
```

This happens when schema objects were created outside Alembic revision tracking, or when a previous database volume survived without a version stamp.

### Safe local-only fix

Use this only when you have confirmed the live schema already matches revision `001_initial_uuid_schema` and you need to align Alembic state without re-running the migration:

```bash
docker compose exec postgres psql -U ghost_sweep -d ghost_sweep -c \
  "INSERT INTO alembic_version (version_num) VALUES ('001_initial_uuid_schema');"
```

Then restart the backend:

```bash
docker compose up -d backend
docker compose logs --tail=100 backend
```

Do not stamp a database whose schema does not match the migration. If the schema is unknown or mismatched, reset the development database instead of stamping.

### Fresh database path

For a new or reset development database, use the normal migration path:

```bash
docker compose up -d postgres
cd backend
alembic upgrade head
```

The backend container entrypoint also runs `alembic upgrade head` on startup. A fresh Postgres volume with no pre-existing tables should migrate cleanly without manual stamping.

## Related documentation

- [database-migrations.md](database-migrations.md)
- [auth-api.md](auth-api.md)
- [api.md](api.md)
