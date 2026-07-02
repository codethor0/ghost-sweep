# Hosting Readiness Spike

Batch 13C docs-only assessment. **No deploy performed.** No cloud resources created.

Baseline commit: `0201b86` (Batch 13B roadmap realignment).

## Status

| Item | State |
| ---- | ----- |
| Public MVP | Live — GitHub Pages + Google Form + manual Sheet moderation |
| Full backend (FastAPI) | Local Docker only |
| Managed Postgres / Redis (production) | Not provisioned |
| Public frontend (Next.js) | Local Docker only; not hosted |
| Sheet import `--apply` | Not implemented; blocked |
| Production import automation | Not enabled |
| Live Sheet Gates 11-live / 12-live | **BLOCKED-LIVE** |

## Current architecture

```text
Public (live today)
  GitHub Pages (static MVP) --> Google Form --> Google Sheet --> manual moderation

Local only (Docker Compose)
  frontend (Next.js :3000) --> backend (FastAPI :8000) --> postgres:15
                                                      --> redis:7

Future (not deployed)
  hosted backend API --> managed Postgres + Redis
  optional hosted frontend (separate decision)
  optional Sheet import apply (blocked; separate maintainer decisions)
```

The public static MVP does **not** require the FastAPI backend. Hosting the backend is a separate milestone for in-app reports, scoring database exposure, moderation UI, and extension API integration.

## Non-goals (Batch 13C)

- No deploy
- No cloud resource creation
- No DNS changes
- No GitHub Pages changes
- No Google Form or Sheet changes
- No production database writes
- No `--apply` or production Sheet import automation
- No live Sheet gate changes
- No backend, frontend, extension, Docker, CI, or schema changes in this batch

## Runtime inventory

Discovered from `docker-compose.yml`, `backend/Dockerfile`, `backend/docker-entrypoint.sh`, `backend/app/config.py`, `backend/app/main.py`, and `.env.example`.

### Backend framework and entrypoint

| Item | Value |
| ---- | ----- |
| Framework | FastAPI (Python 3.11) |
| ASGI server | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Container port | 8000 |
| Startup | `alembic upgrade head` then uvicorn (`backend/docker-entrypoint.sh`) |
| API prefix | `/api/v1` (configurable via settings; default in code) |
| Health endpoints | `GET /health`, `GET /` |

### Database

| Item | Value |
| ---- | ----- |
| Engine | PostgreSQL 15 |
| Driver | SQLAlchemy 2.0 async via `asyncpg` |
| Connection URL | `DATABASE_URL` — format `postgresql+asyncpg://user:pass@host:port/dbname` |
| Migrations | Alembic; revisions `001_initial_uuid_schema`, `002_employer_claim_constraints` |
| Local Compose DB | `ghost_sweep` on postgres service |

### Redis

| Item | Value |
| ---- | ----- |
| Version | Redis 7 (Compose image) |
| Connection URL | `REDIS_URL` — format `redis://host:port/db` |
| Uses | Auth rate limiting; refresh token storage (per project docs) |

### Docker Compose services (local)

| Service | Image / build | Host port | Notes |
| ------- | ------------- | --------- | ----- |
| postgres | postgres:15 | 5432 | Persistent volume `postgres_data` |
| postgres_test | postgres:15 | 5433 | Test DB only |
| redis | redis:7 | 6379 | No persistence in default Compose |
| backend | `./backend` Dockerfile | 8000 | Depends on postgres + redis healthy |
| frontend | `./frontend` Dockerfile | 3000 | `NEXT_PUBLIC_API_BASE_URL` points at backend |

### Environment variables (confirmed in repo)

| Variable | Required | Scope | Purpose |
| -------- | -------- | ----- | ------- |
| `ENVIRONMENT` | Yes (production deploy) | Backend | `development`, `staging`, or `production` — validated in `Settings` |
| `DATABASE_URL` | Yes | Backend | Async Postgres connection string |
| `REDIS_URL` | Yes | Backend | Redis connection string |
| `JWT_SECRET_KEY` | Yes in staging/production | Backend | Min 32 characters; required when `ENVIRONMENT` is `staging` or `production` |
| `CORS_ORIGINS` | Yes (production deploy) | Backend | JSON list of allowed origins; local default `["http://localhost:3000"]` |
| `TEST_DATABASE_URL` | Dev/test only | pytest | Not used in production deploy |
| `TEST_REDIS_URL` | Dev/test only | pytest | Not used in production deploy |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend build | Frontend | Public API base URL baked at build time |

### Settings with code defaults (no separate env var in `.env.example`)

| Setting | Default | Notes |
| ------- | ------- | ----- |
| `JWT_ALGORITHM` | HS256 | Not overridden in `.env.example` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | TBD whether env exposure is needed for production |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 14 | TBD whether env exposure is needed for production |
| `AUTH_RATE_LIMIT_PER_MINUTE` | 20 | TBD whether env exposure is needed for production |
| `DEBUG` | false | TBD for production observability policy |

### Local-only assumptions today

- Backend and frontend run on localhost with Compose service hostnames (`postgres`, `redis`).
- CORS allows `http://localhost:3000` only in default Compose env.
- JWT secret has a development-only default when `ENVIRONMENT=development` and secret is unset (`backend/app/config.py`).
- Demo seed script refuses non-development environments (`backend/scripts/seed_demo_data.py`).
- Sheet import `--apply` is not implemented; design requires local-only guard when implemented (`sheet-import-apply-design.md` section 16).
- Public MVP static site has no backend dependency.

### CORS and frontend integration

- Backend uses FastAPI `CORSMiddleware` with `allow_credentials=True`.
- Production deploy must set `CORS_ORIGINS` to explicit hosted frontend origin(s) — not `localhost`.
- Frontend is Next.js 16 server mode; hosting the frontend is a **separate** decision from backend API hosting (Render/Vercel/other).
- Extension currently opens local frontend with query params only; no backend API calls.

### Auth and session

- JWT access tokens; refresh tokens stored in Redis by SHA-256 hash.
- Refresh endpoint does not rotate refresh token until expiry or logout (documented in `implementation-status.md`).
- Auth rate limiting uses Redis (`auth_rate_limit_per_minute`).

### Migration / Alembic readiness

- Migrations run automatically on container start via `docker-entrypoint.sh`.
- **Production consideration:** running migrations on every web container start can race if multiple instances scale horizontally; a future deploy batch should decide migrate-on-start vs one-shot release job.
- See [database-migrations.md](database-migrations.md).

### Logging and observability gaps

- Backend uses Python `logging` at INFO in `main.py`; no structured logging or APM integration documented.
- `/health` returns service name and `"ok"` only — does **not** verify Postgres or Redis connectivity.
- No production metrics, tracing, or alerting plan in repo.

### Security-sensitive variables

| Secret / sensitive config | Handling |
| ------------------------- | -------- |
| `JWT_SECRET_KEY` | Platform secret store; min 32 chars; never commit |
| `DATABASE_URL` | Contains credentials; platform secret store |
| `REDIS_URL` | May contain password if provider requires auth; platform secret store |
| Postgres credentials | Managed by hosting provider or secret injection |

### What must remain local-only for now

- Sheet import `--apply` (blocked; design local-only until separate approval)
- Production Sheet import automation
- Demo seed script (`ENVIRONMENT=development` only)
- Live Sheet export verification artifacts (outside repo)
- Any hosted DB apply without explicit maintainer batch approval

## Environment and secrets checklist

Use this before a future deploy batch. Mark TBD items during platform selection.

### Backend (required for production API)

- [ ] `ENVIRONMENT=production` (or `staging` for pre-prod)
- [ ] `DATABASE_URL` — managed Postgres async URL (`postgresql+asyncpg://...`)
- [ ] `REDIS_URL` — managed Redis URL
- [ ] `JWT_SECRET_KEY` — cryptographically random, minimum 32 characters
- [ ] `CORS_ORIGINS` — JSON list of allowed frontend origin(s); no wildcard with credentials

### Backend (optional / TBD)

- [ ] `DEBUG` — confirm `false` in production
- [ ] Token TTL overrides — TBD if env vars should be exposed
- [ ] Rate limit overrides — TBD if env vars should be exposed

### Frontend (if hosted separately)

- [ ] `NEXT_PUBLIC_API_BASE_URL` — HTTPS URL of hosted backend API

### Infrastructure (platform-managed)

- [ ] Postgres 15 instance provisioned
- [ ] Redis 7 instance provisioned
- [ ] TLS termination configured for public API
- [ ] Secrets stored in platform secret manager (not in git)

### Explicitly out of scope for first backend deploy

- [ ] Sheet import `--apply` credentials or automation
- [ ] Production import from Google Sheet
- [ ] Google Sheets API OAuth

## Platform comparison

Qualitative assessment only. Pricing and free-tier limits change; verify on provider sites before committing.

| Criterion | Render | Fly.io | Railway |
| --------- | ------ | ------ | ------- |
| FastAPI fit | Strong — native Python web service, Docker or buildpack | Strong — Docker-based Machines | Strong — Docker/Nixpacks deploy |
| Managed Postgres | Yes (Render Postgres) | Yes (Fly Postgres) | Yes (Railway Postgres plugin) |
| Managed Redis | Yes (Render Key Value / Redis-compatible) | Yes (Upstash integration; Fly Redis legacy patterns) | Yes (Railway Redis plugin) |
| Secret management | Environment groups / service env vars | `fly secrets` | Project/service variables |
| Deployment model | Git push or Docker image to web service | `fly deploy` CLI / CI to Machines | GitHub-connected deploy |
| Health checks | HTTP health check path configurable | HTTP checks on services | Health check support on services |
| Background workers | Separate worker service type | Separate process groups / Machines | Separate services possible |
| Ops complexity | Low — familiar PaaS model | Medium–high — regions, volumes, networking | Low–medium — fast setup |
| Migration from local Docker | Replace Compose services with managed DB/Redis + web service using existing `backend/Dockerfile` | Same; more manual networking/TLS tuning | Same; watch env var governance |
| ghost-sweep fit | **Best MVP simplicity** — web + Postgres + Redis + secrets in one place | Good when infra control matters; steeper learning curve | Good for rapid prototype; tighten cost and secret governance |
| Caveats | Cold starts on free/low tiers; review egress and DB connection limits | More concepts (apps, machines, regions); ops ownership | Monitor usage/cost; confirm Postgres 15 and Redis 7 availability on chosen plan |
| Security notes | TLS by default on `*.onrender.com`; restrict CORS; use private DB links where offered | WireGuard/private networking options; secrets via CLI | Use private networking where available; avoid logging secrets |

## Recommended MVP hosting path

**Primary recommendation: Render** for the first public backend API deploy spike (implementation batch, not this docs batch).

**Why Render:**

1. Matches the existing Docker workflow — deploy `backend/Dockerfile` as a web service with minimal adaptation.
2. Managed Postgres and Redis-compatible services align with Compose dependencies without running DB inside the app container.
3. Environment variables and secret groups map directly to confirmed settings (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `ENVIRONMENT`).
4. Built-in HTTP health checks can target `GET /health` already implemented in `backend/app/main.py`.
5. Lower operational surface than Fly.io for a maintainer-first MVP.

**Conditional alternatives:**

- **Fly.io** — choose if multi-region placement, private networking, or fine-grained machine control is required early; accept higher ops burden.
- **Railway** — choose for fastest throwaway staging; add explicit cost caps and secret review before production.

**Scope of first deploy batch (future, not 13C):**

- Backend API only (FastAPI + managed Postgres + managed Redis).
- Run Alembic migrations with an explicit strategy (single release job preferred over N parallel migrate-on-start instances).
- Do **not** include Sheet import `--apply`, production import automation, or live Sheet gate work.
- Frontend hosting remains a **follow-on** decision (Render web service, Vercel, or continue local-only while API is validated).

## Security requirements before deploy

1. **Generate production secrets** — new `JWT_SECRET_KEY` (32+ chars); unique DB credentials from provider.
2. **No committed secrets** — `.env` stays gitignored; use platform secret stores only.
3. **CORS / allowed origins** — set explicit HTTPS frontend origin(s); reject localhost in production config.
4. **Database migration plan** — document one-shot `alembic upgrade head` vs entrypoint behavior; test against staging first.
5. **Backup / restore** — enable managed Postgres backups; document restore drill (TBD per provider).
6. **Logging / monitoring** — define minimum: request errors, auth failures, migration failures; `/health` is not dependency-aware today.
7. **Rate limiting / abuse** — Redis-backed auth rate limit exists; review whether edge rate limits (platform or CDN) are needed.
8. **Branch protection / deploy protection** — enable before multi-maintainer deploys ([repository-security.md](repository-security.md)).
9. **Rollback plan** — retain previous container image; document DB migration rollback limits (Alembic downgrade policy TBD).

## Deployment readiness gates

Future deploy batch must not proceed until maintainer signs each item:

| # | Gate | Batch 13C status |
| - | ---- | ---------------- |
| 1 | Platform selected (Render recommended) | Pending maintainer |
| 2 | Secrets checklist finalized | Documented above; values not created |
| 3 | Production database plan approved | Pending |
| 4 | CORS / origin policy approved | Pending |
| 5 | Health check path confirmed (`GET /health`) | Available in code |
| 6 | Migration strategy confirmed | Pending — entrypoint runs migrate today |
| 7 | Rollback plan confirmed | Pending |
| 8 | No `--apply` or production import in scope | **Required** — out of scope |
| 9 | Live Sheet gates remain out of scope unless separately approved | **Required** — BLOCKED-LIVE |

### Sheet import / Section 18 reminder

- Offline Gates 11/12: **ACCEPTED-MVP** (Batch 12S).
- Live Gates 11-live / 12-live: **BLOCKED-LIVE**.
- `--apply`: blocked.
- Hosted import phase in [sheet-import-design.md](sheet-import-design.md) (import doc phase 13A) is **not** part of backend hosting deploy.

## Recommended next batch

| Option | Batch | Scope |
| ------ | ----- | ----- |
| A (recommended) | **13D** | Platform-specific deployment plan for Render — service layout, env var matrix, staging vs production, still **no deploy** |
| B | **13D** | Moderation UI scoping (Issue #7) — docs-only product design |

Execute **13D Render deployment plan** if the goal is to reach a safe staging deploy next. Execute **13D moderation UI scoping** if product design should lead hosting.

## Related documents

- [post-launch-roadmap.md](post-launch-roadmap.md)
- [project-operations-plan.md](project-operations-plan.md)
- [database-migrations.md](database-migrations.md)
- [repository-security.md](repository-security.md)
- [local-docker-validation.md](local-docker-validation.md)
- [sheet-import-apply-design.md](sheet-import-apply-design.md) section 16
- [implementation-status.md](implementation-status.md)
