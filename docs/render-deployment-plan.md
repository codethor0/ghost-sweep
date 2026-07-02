# Render Deployment Plan

Batch 13D docs-only plan. **No deploy performed.** No Render resources created.

Baseline: [hosting-readiness-spike.md](hosting-readiness-spike.md) (Batch 13C, commit `2b4d7c7`).

## Status

| Item | State |
| ---- | ----- |
| Render services | Not created |
| Managed Postgres / Redis (Render) | Not provisioned |
| Public backend API | Local Docker only |
| Public MVP | GitHub Pages + Google Form + manual Sheet moderation |
| Sheet import `--apply` | Not implemented; **blocked** |
| Production import automation | **Not enabled** |
| Live Gate 11 / 12 | **BLOCKED-LIVE** |
| Offline Sheet Gates 11/12 (MVP) | **ACCEPTED-MVP** (Batch 12S) |

## Current architecture

```text
Live today
  GitHub Pages --> Google Form --> Google Sheet --> manual moderation

Local Docker (unchanged)
  frontend (:3000) --> backend FastAPI (:8000) --> Postgres 15
                                               --> Redis 7

Planned on Render (not provisioned)
  ghost-sweep-api (web service, Docker)
        |--> Render Postgres 15
        |--> Render Key Value / Redis-compatible
```

Source of truth for runtime variables: `backend/app/config.py`, `.env.example`, `docker-compose.yml`, `backend/docker-entrypoint.sh`.

## Non-goals (Batch 13D)

- No deploy
- No Render dashboard changes
- No cloud resource creation
- No DNS changes
- No GitHub Pages changes
- No Google Form or Sheet changes
- No production database writes
- No `--apply` or production Sheet import automation
- No live Sheet gate changes
- No frontend hosting migration in this batch
- No backend, frontend, Docker, CI, or schema changes

## Proposed Render service layout

### Services (staging and production are separate Render projects or environments)

| Render resource | Purpose | Notes |
| --------------- | ------- | ----- |
| **Web service** `ghost-sweep-api` | FastAPI backend | Docker deploy from `backend/Dockerfile`; port 8000; root directory `backend/` or repo root with Dockerfile path |
| **PostgreSQL** | Primary database | Postgres 15; private connection string injected as `DATABASE_URL` |
| **Key Value / Redis** | Auth rate limit + refresh tokens | Redis-compatible URL injected as `REDIS_URL` |

### Deploy model

- **GitHub-connected** deploy from `codethor0/ghost-sweep` `main` branch (implementation batch only; not configured in 13D).
- **Staging first:** create staging Postgres, Redis, and web service; validate migrations, health, auth, and CORS before any production promotion.
- **Production later:** separate Render Postgres/Redis/web service (or separate project); distinct secrets; no shared JWT secret with staging.

### Health check

| Setting | Value |
| ------- | ----- |
| Path | `/health` |
| Method | GET |
| Expected | HTTP 200, JSON `status: ok` |

Render health check uses the lightweight endpoint in `backend/app/main.py`. It does **not** prove Postgres or Redis connectivity.

### Scaling (initial policy)

- **Staging:** single instance (free or starter tier TBD by maintainer).
- **Production:** start single instance until migration strategy is changed away from migrate-on-start (see Migration strategy).
- Do not enable autoscaling until migration runs outside the web entrypoint or uses a single-release job.

## Environment matrix

Variables confirmed in repo only. Secret **values** are never stored in git or this document.

| Variable | development (local Docker) | staging (Render) | production (Render) |
| -------- | -------------------------- | ---------------- | ------------------- |
| `ENVIRONMENT` | `development` | `staging` | `production` |
| `DATABASE_URL` | Compose postgres URL | Render Postgres internal URL, `postgresql+asyncpg://...` | Separate Render Postgres URL |
| `REDIS_URL` | Compose redis URL | Render Key Value URL | Separate Key Value URL |
| `JWT_SECRET_KEY` | Optional dev default in code | **Required** — unique random 32+ chars | **Required** — unique random 32+ chars, distinct from staging |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | TBD — approved staging frontend origin(s) only | TBD — approved production origin(s) only |
| `DEBUG` | TBD | `false` (recommended) | `false` (recommended) |
| `TEST_DATABASE_URL` | Local pytest | Not set | Not set |
| `TEST_REDIS_URL` | Local pytest | Not set | Not set |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | TBD when frontend wired to staging API | TBD when frontend wired to production API |

### Staging CORS notes

- Public MVP at `https://codethor0.github.io/ghost-sweep/` does **not** call the backend today.
- Do not add GitHub Pages origin to `CORS_ORIGINS` until a maintainer-approved client (hosted frontend or explicit MVP integration) requires it.
- Staging may initially allow only `http://localhost:3000` for local frontend testing against staging API, or a dedicated staging frontend URL — **maintainer approval required**.

## Secrets handling

| Rule | Detail |
| ---- | ------ |
| Storage | Render service environment variables and/or environment groups only |
| Never commit | No `.env`, no secrets in docs, issues, or CI logs |
| `JWT_SECRET_KEY` | Generate per environment (`openssl rand -base64 48` or platform generator); minimum 32 characters; staging and production must differ |
| `DATABASE_URL` | Provided by Render Postgres; use internal URL for web service in same region |
| `REDIS_URL` | Provided by Render Key Value; treat as secret if password embedded |
| Rotation | Rotate `JWT_SECRET_KEY` on compromise; invalidates existing refresh tokens in Redis; plan maintenance window |
| Review | No secret values in Render build logs; confirm `ENVIRONMENT` is not logged with secrets |

Production secret values are **not** copied into repository documentation.

## Migration strategy

### Current behavior (local Docker)

`backend/docker-entrypoint.sh` runs:

```text
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Migrations run on **every container start**.

### Options for Render

| Approach | Pros | Cons | 13D recommendation |
| -------- | ---- | ---- | ------------------ |
| **A. Keep entrypoint migrate-on-start** | No repo change; matches local Docker | Race if multiple instances start together; migrate repeats each deploy/restart | **Accept for staging single-instance first deploy** |
| **B. Render Pre-Deploy Command** | Runs once per deploy before new version serves traffic | Requires Dockerfile/entrypoint change in a **future approved batch** to remove duplicate migrate | Preferred **before production scale-out** |
| **C. One-shot manual shell job** | Full maintainer control | Manual step; easy to forget | Acceptable for first staging bootstrap only |

### Recommended first staging approach

1. **Single web service instance** on staging.
2. Use **existing Docker entrypoint** (option A) for the first staging deploy implementation batch — no Docker edits until maintainer approves option B.
3. Before first deploy: confirm Render Postgres backup/snapshot policy enabled.
4. Maintainer reviews migration logs after first deploy (`001_initial_uuid_schema`, `002_employer_claim_constraints`).
5. Before production: move to **Pre-Deploy Command** or dedicated release job (option B) if more than one instance is planned.

### Migration safety rules

- Backup Postgres before first migration on staging and before every production migration.
- Review Alembic output in deploy logs.
- No destructive migrations without maintainer approval and tested downgrade plan.
- Do not run `scripts/seed_demo_data.py` on staging or production (`ENVIRONMENT` guard in script).
- Sheet import `--apply` must **not** run against staging or production in hosting deploy batches.

### Rollback (migration failure)

1. Stop or roll back web service to previous deploy image.
2. If schema partially applied: restore Postgres from pre-migration backup (Render snapshot or manual dump).
3. Document whether Alembic downgrade is available for the failing revision (project policy TBD per [database-migrations.md](database-migrations.md)).

## Health checks

| Endpoint | Behavior today | Render use |
| -------- | -------------- | ---------- |
| `GET /health` | Returns `status: ok`, service name | **Use for Render health check** |
| `GET /` | API metadata | Optional smoke test |
| DB/Redis probe | **Not implemented** | Future enhancement; do not implement in Batch 13D |

A passing `/health` does **not** guarantee database or Redis availability. Post-deploy smoke tests should include authenticated API paths in a future implementation batch.

## CORS and frontend integration

- Backend: `CORSMiddleware` with `allow_credentials=True` (`backend/app/main.py`).
- `CORS_ORIGINS` must list only maintainer-approved HTTPS origins in staging/production.
- Localhost defaults from Compose are **not** production policy.
- GitHub Pages static MVP origin requires explicit review before inclusion — static site currently has no backend calls.
- Frontend `NEXT_PUBLIC_API_BASE_URL` is a **build-time** variable; pointing a hosted frontend at Render API is a separate batch from backend-only staging.

## Security gates before deploy

Maintainer must sign each gate before a **future implementation batch** creates Render resources:

| # | Gate |
| - | ---- |
| 1 | Branch protection or ruleset decision ([repository-security.md](repository-security.md)) |
| 2 | Secret inventory finalized (this document + hosting spike checklist) |
| 3 | Staging `JWT_SECRET_KEY` generated (not in repo) |
| 4 | Staging Postgres provisioned and backup policy confirmed |
| 5 | Staging Redis / Key Value provisioned |
| 6 | CORS policy approved for staging |
| 7 | Migration strategy approved (single-instance + entrypoint migrate for first staging) |
| 8 | Health check path `/health` confirmed |
| 9 | Logging/monitoring baseline selected (Render logs minimum) |
| 10 | Rollback plan approved (this document) |
| 11 | **No `--apply` in deploy scope** |
| 12 | **No production Sheet import automation in deploy scope** |
| 13 | **Live Sheet gates remain out of scope** unless separately approved |

Deploy implementation requires explicit maintainer approval per AGENTS.md (Docker/deployment config changes).

## Staging deployment checklist

**Documentation only — do not execute in Batch 13D.**

- [ ] Maintainer approval for Render staging batch recorded
- [ ] Create Render Postgres 15 (staging)
- [ ] Create Render Key Value / Redis (staging)
- [ ] Create web service from `backend/Dockerfile`; set health check `/health`
- [ ] Set `ENVIRONMENT=staging`
- [ ] Inject `DATABASE_URL` (asyncpg format), `REDIS_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`
- [ ] Enable Postgres backups
- [ ] Deploy from approved commit; capture migration logs
- [ ] Smoke test: `GET /health`, `GET /`, auth register/login against staging (manual)
- [ ] Confirm no Sheet import `--apply` scripts or jobs configured
- [ ] Document staging API URL for future frontend wiring (do not publish until policy approved)

## Production promotion checklist

**Requires successful staging validation first.**

- [ ] Staging sign-off documented
- [ ] Separate production Postgres and Redis (no shared credentials with staging)
- [ ] New production `JWT_SECRET_KEY` (distinct from staging)
- [ ] Production `CORS_ORIGINS` approved
- [ ] Migration strategy reviewed (prefer Pre-Deploy Command if multi-instance)
- [ ] Production backups and restore drill documented
- [ ] Rollback owner assigned
- [ ] Confirm `--apply` and production import remain blocked
- [ ] Live Gate 11 / 12 remain **BLOCKED-LIVE** unless separately amended

## Rollback plan

| Scenario | Action |
| -------- | ------ |
| Bad application deploy | Render: rollback to previous successful deploy / image |
| Migration failure | Stop traffic; restore Postgres from pre-migration backup; rollback web service |
| Exposed secret | Rotate `JWT_SECRET_KEY`, `DATABASE_URL` password, or Redis credentials; redeploy |
| Bad CORS / accidental public exposure | Remove origin from `CORS_ORIGINS`; redeploy; disable auto-deploy until fixed |
| Frontend calling wrong API | Revert `NEXT_PUBLIC_API_BASE_URL` build or disable client |

## Risks

| Risk | Mitigation |
| ---- | ---------- |
| Accidental production DB writes | Staging first; separate databases; no `--apply` in deploy scope |
| Permissive CORS | Explicit origin list; no wildcard with credentials |
| Weak JWT secret | Enforce 32+ chars; platform-generated secrets; staging/production unique |
| Migration failure | Backup before migrate; single instance first; review logs |
| Missing Redis | Web service fails auth paths; verify `REDIS_URL` before go-live |
| `/health` false confidence | Add manual DB/Redis smoke tests in implementation batch |
| Cost / resource drift | Label staging resources; review Render dashboard monthly |
| Premature `--apply` or import | Keep blocked; do not add import cron or `--apply` to Render services |
| Live Sheet proof confusion | Hosting deploy does **not** satisfy Live Gates 11-live / 12-live |

## Recommended next batch

| Priority | Batch | Scope |
| -------- | ----- | ----- |
| A | **13E** | Moderation UI scoping (Issue #7) — docs-only |
| B | **13E** | Repository security settings plan — branch protection before Render staging implementation |
| C | **14A** | Render staging **implementation** — creates resources; requires maintainer approval for Docker/deploy changes |

Batch 13D does **not** authorize Batch 14A. A separate maintainer decision is required before any Render resource is created.

## Related documents

- [hosting-readiness-spike.md](hosting-readiness-spike.md)
- [post-launch-roadmap.md](post-launch-roadmap.md)
- [database-migrations.md](database-migrations.md)
- [repository-security.md](repository-security.md)
- [sheet-import-apply-design.md](sheet-import-apply-design.md) section 16
- [implementation-status.md](implementation-status.md)
