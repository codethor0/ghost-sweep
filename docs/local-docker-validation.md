# Local Docker Validation Checkpoint

This document records live-validated milestones for ghost-sweep on Docker Compose.

Latest validation baseline: commit `fee68e1` (Batch 6F on `main`; includes Batch 6D offline URL validation and prior API/frontend scope).

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

## Domain endpoints (Batch 5)

Batch 5 domain APIs are committed at `feefc19`. Public reads do not require authentication; report and vote writes require a bearer access token from the auth flow above.

Replace placeholder UUIDs with values returned by earlier requests or seeded test data in your database.

```bash
# Public reads
curl -s http://localhost:8000/api/v1/companies | jq .
curl -s http://localhost:8000/api/v1/companies/{company_id} | jq .
curl -s http://localhost:8000/api/v1/companies/{company_id}/integrity-score | jq .

curl -s http://localhost:8000/api/v1/job-postings/{job_posting_id} | jq .
curl -s http://localhost:8000/api/v1/job-postings/{job_posting_id}/risk-score | jq .

# Authenticated writes (set ACCESS_TOKEN from register or login)
ACCESS_TOKEN="<access_token>"
JOB_POSTING_ID="<job_posting_uuid>"

curl -s -X POST http://localhost:8000/api/v1/reports \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"job_posting_id\":\"${JOB_POSTING_ID}\",\"report_type\":\"stale_posting\",\"description\":\"The posting remained active without recruiter follow-up for several months.\"}" \
  | jq .

REPORT_ID="<report_uuid_from_create_response>"

curl -s "http://localhost:8000/api/v1/reports?job_posting_id=${JOB_POSTING_ID}" | jq .
curl -s http://localhost:8000/api/v1/reports/${REPORT_ID} | jq .

curl -s -X POST "http://localhost:8000/api/v1/reports/${REPORT_ID}/votes" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"vote":"up"}' \
  | jq .
```

| Endpoint | Auth | Expected result |
| -------- | ---- | --------------- |
| `GET /api/v1/companies` | No | HTTP 200, paginated company list |
| `GET /api/v1/companies/{id}` | No | HTTP 200 or 404 |
| `GET /api/v1/companies/{id}/integrity-score` | No | HTTP 200 score breakdown or 404 |
| `GET /api/v1/job-postings/{id}` | No | HTTP 200 or 404 |
| `GET /api/v1/job-postings/{id}/risk-score` | No | HTTP 200 score breakdown or 404 |
| `POST /api/v1/reports` | Bearer | HTTP 201, report with `status: pending` |
| `GET /api/v1/reports?job_posting_id={uuid}` | No | HTTP 200 paginated list or 404 |
| `GET /api/v1/reports/{id}` | No | HTTP 200 or 404 |
| `POST /api/v1/reports/{id}/votes` | Bearer | HTTP 201 or 409 on duplicate vote |

See [domain-api.md](domain-api.md) for request and response details.

## Batch 6B endpoints (employer and moderation)

Batch 6B APIs are committed at `27dada0`. Admin and employer flows require SQL bootstrap in development:

```sql
UPDATE users SET is_admin = true WHERE email = 'your@email.com';
```

Validated live (with bootstrapped company and job posting data):

| Endpoint | Auth | Expected result |
| -------- | ---- | --------------- |
| `POST /api/v1/employer-claims` | Bearer | HTTP 201; requires `verification_documents` array |
| `POST /api/v1/employer-claims/{id}/approve` | Admin bearer | HTTP 200 |
| `GET /api/v1/moderation/reports` | Admin bearer | HTTP 200 |
| `GET /api/v1/moderation/reports` | Non-admin bearer | HTTP 403 |
| `POST /api/v1/moderation/reports/{id}/verify` | Admin bearer | HTTP 200 |
| `POST /api/v1/moderation/reports/{id}/dismiss` | Admin bearer | HTTP 200 |
| `POST /api/v1/reports/{id}/responses` | Approved employer | HTTP 201; may move report to `disputed` |

See [employer-api.md](employer-api.md) and [moderation-api.md](moderation-api.md).

## Demo seed (local development only)

When the companies list is empty, run the idempotent demo seed from the backend directory:

```bash
cd backend
python3.11 scripts/seed_demo_data.py
```

This creates one demo company and job posting when `ENVIRONMENT=development`. It refuses to run in staging or production.

## SQL bootstrap (local validation only)

When testing employer or moderation flows against a fresh database, SQL bootstrap is acceptable for local validation but is **not** product UX. Record commands used in validation logs.

Example (replace UUIDs and emails):

```sql
INSERT INTO companies (id, name, domain, locations)
VALUES (gen_random_uuid(), 'E2E Test Corp', 'e2e.example.com', '[]'::jsonb);

INSERT INTO job_postings (id, company_id, title, url, detected_at, last_seen_at)
VALUES (
  gen_random_uuid(),
  '<company_uuid>'::uuid,
  'E2E Role',
  'https://e2e.example.com/jobs/1',
  now(),
  now()
);

UPDATE users SET is_admin = true WHERE email = 'admin@example.com';
```

Employer claims require `verification_documents` in the JSON body. See [employer-api.md](employer-api.md).

Redact access and refresh tokens from validation reports. See [validation-artifacts.md](validation-artifacts.md).

## Frontend status (Batch 6C)

The frontend container serves at `http://localhost:3000`.

Validated pages (curl or browser):

| Page | Expected |
| ---- | -------- |
| `/` | Home, health panel matching `{status, service}` |
| `/register`, `/login` | Auth forms |
| `/dashboard` | Profile when signed in; sign-in prompt when not |
| `/companies` | Company list from API |
| `/companies/{id}` | Detail and integrity score |
| `/postings/{id}` | Detail, risk score, deferred notices |
| `/postings/{id}/report` | Report form when signed in |
| `/?posting_url=...` | Handoff notice; does not claim URL lookup is wired |

Frontend access tokens are stored in React state only and are lost on page refresh. Refresh token handling is not wired in the UI.

## Public MVP (static site)

The free public launch path uses `public-mvp/`, not the Next.js frontend.

| Item | Detail |
| ---- | ------ |
| Location | `public-mvp/index.html`, `public-mvp/styles.css` |
| Hosting | GitHub Pages (static only); configure Settings -> Pages -> /public-mvp |
| Backend calls | None |
| Report intake | Google Form placeholder URL; manual Sheet review |
| Full app | FastAPI/Postgres/Redis remains local Docker only |

Local preview:

```bash
python3 -m http.server 8080 --directory public-mvp
curl -I http://localhost:8080/
curl -sS http://localhost:8080/ | grep -i "Submit a report"
```

Validation:

```bash
python3.11 scripts/validate_public_mvp.py
```

See [free-public-launch-plan.md](free-public-launch-plan.md) and [google-form-intake-spec.md](google-form-intake-spec.md).

## Extension status

The browser extension exists under `extension/` for Chrome and Firefox Manifest V3.

The popup reads the active tab URL and opens the frontend with `?posting_url=`. Extension smoke tests validate manifest structure only. Browser manual testing and backend API integration remain deferred. Batch 6D added an offline URL validation helper only; it is not wired to the extension or API.

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
- [domain-api.md](domain-api.md)
- [api.md](api.md)
- [validation-artifacts.md](validation-artifacts.md)
