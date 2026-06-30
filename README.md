# ghost-sweep

ghost-sweep is an open-source, community-driven Job Integrity Database that helps job seekers evaluate hiring transparency using evidence-based reports, transparent integrity scores, and employer response workflows.

## Problem

Job seekers often invest time in postings that remain open without hiring intent, receive no recruiter follow-up, or are reposted repeatedly without closure. Hiring transparency is uneven, and public information is fragmented across boards, employer sites, and anecdotal reports.

## Solution

ghost-sweep collects structured, evidence-backed reports about job postings and companies, calculates documented integrity scores, and gives employers a path to verify active roles, respond to reports, and dispute incorrect information.

The platform uses risk-signal language. It does not make unsupported legal accusations.

## Architecture

```text
ghost-sweep/
  backend/     FastAPI API, scoring engine, auth, moderation services
  frontend/    Next.js web application (local Docker; server-mode)
  public-mvp/  Static GitHub Pages landing site (free public MVP)
  extension/   Manifest V3 browser extension for job board overlays
  docs/        Architecture, API, scoring, moderation, legal guidance
  .github/     CI workflows and community templates
```

Data stores:

- PostgreSQL 15 for primary records
- Redis 7 for auth rate limiting and refresh token storage

## Tech stack

Backend: Python 3.11, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, PostgreSQL 15, Redis 7

Frontend: Next.js 14, React, TypeScript strict mode, Tailwind CSS

Extension: Chrome and Firefox Manifest V3

## Quick start

```bash
cp .env.example .env
docker compose up -d postgres postgres_test redis
docker compose up --build backend frontend
```

Optional local demo data (development only):

```bash
cd backend
python3.11 scripts/seed_demo_data.py
```

This creates a demo company and job posting when `ENVIRONMENT=development`. It is idempotent and refuses to run in staging or production.

For employer/moderation live validation without the seed script, see SQL bootstrap examples in [docs/local-docker-validation.md](docs/local-docker-validation.md). SQL bootstrap is for local validation only, not product UX.

Validation artifacts must redact tokens. See [docs/validation-artifacts.md](docs/validation-artifacts.md).

API: http://localhost:8000  
Frontend: http://localhost:3000

## Public MVP (static site)

The free public launch path uses a standalone static site in `public-mvp/`, not the full Next.js app.

| Layer | Hosting | Status |
| ----- | ------- | ------ |
| Public landing + report CTA | GitHub Pages (`public-mvp/`) | Static site files are ready; replace the Google Form URL before enabling GitHub Pages |
| Report intake | Google Form -> Google Sheet | Temporary; manual review |
| Full app (FastAPI/Postgres/Redis) | Local Docker only | Batch 6B/6C; not publicly hosted |
| Live scoring database | Not hosted | Deferred |

GitHub Pages serves static HTML/CSS/JS only. It cannot run FastAPI, PostgreSQL, or Redis. The Batch 6C Next.js frontend is server-mode and is not GitHub Pages-ready without separate changes.

Preview the static MVP locally:

```bash
python3 -m http.server 8080 --directory public-mvp
```

Validate before deploy:

```bash
python3.11 scripts/validate_public_mvp.py
```

See [docs/free-public-launch-plan.md](docs/free-public-launch-plan.md), [docs/google-form-intake-spec.md](docs/google-form-intake-spec.md), and [docs/public-launch-checklist.md](docs/public-launch-checklist.md).

The Google Form URL in `public-mvp/index.html` is a placeholder until the real form is created. Raw applicant emails must not be published. The repository is private. Public launch is not started and the launch checklist remains incomplete. Private collaborators can onboard via `docs/contributor-onboarding.md`.

## Current project status

Latest pushed baseline: Batch 6F contributor-readiness sync on `main` (includes Batch 6E at `6074691`).

Batches 6A through 6E are committed on `main`. Batch 6F adds post-6E validation, docs sync, and launch preflight. This is active development, not a release-ready product. Public launch is not started.

**Repository:** private. GitHub Pages is not enabled. Public MVP static files exist in `public-mvp/` but are not live.

**CI:**

- GitHub Actions workflow is aligned with verified local backend gates (Python 3.11, postgres:15, redis:7, coverage >= 80%, advisory-only pip-audit for documented deferred advisories).
- GitHub Actions is blocked by account billing/spending limits before job steps execute. This is an infrastructure blocker, not evidence of failing tests. Local verification is the source of truth until billing is resolved.

**Implemented backend (through Batch 6B):**

- Auth: register, login, `/me`, refresh, logout
- Auth rate limiting
- Company read APIs
- Job posting read APIs
- Report create/read/list
- Votes
- Employer claims (submit, admin approve/reject, migration 002 constraints)
- Moderation queue
- Report verify/dismiss
- Employer responses (auto-dispute from `pending` or `verified`)
- Scoring recalculation and score snapshots
- Audit logging (reports, votes, claims, moderation, employer responses)

**Job URL validation (Batch 6D foundation, offline only):**

- Pure Python helper module: `backend/app/services/job_url_validation.py`
- Normalizes http/https URLs and detects likely ATS or career-page providers
- Unit tests only; not wired to backend API routes; no network calls

**Contributor readiness (Batch 6E complete):**

- 22 GitHub labels live; Issue #1 labeled for first contributor lane
- GitHub issue templates, PR template, CODEOWNERS, label taxonomy doc
- CONTRIBUTING and onboarding doc polish; no application behavior changes
- Private collaborator Write invite for Greg (`gmcguirk-contractor`) pending acceptance; not Admin/Maintain

**Implemented frontend (Batch 6C):**

- API client for existing backend read and write endpoints
- Register and login forms
- In-memory access token session (React state only; lost on page refresh)
- Dashboard (`GET /api/v1/auth/me`)
- Companies list and detail with integrity scores
- Job posting detail with risk scores
- Report submission form (`POST /api/v1/reports`)
- Home health probe and extension `posting_url` handoff display

**Scaffold (not backend-wired):**

- Browser extension: MV3 popup reads active tab URL and opens frontend with `?posting_url=`; no backend API calls

**Deferred:**

- Evidence file upload
- Company and job posting write APIs (public)
- Extension backend API integration
- Wiring job URL validation into API or intake flows
- Frontend moderation, employer, and admin UI
- Frontend refresh-token handling
- Release hardening
- Dependency audit advisories (see [docs/dependency-audit.md](docs/dependency-audit.md))

GitHub repository: https://github.com/codethor0/ghost-sweep (private)

Live Docker validation notes: [docs/local-docker-validation.md](docs/local-docker-validation.md)

## Local development

Backend:

```bash
cd backend
python3.11 -m pip install -e ".[dev]"
pytest tests/test_scoring.py
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Testing

Backend verification:

```bash
cd backend && python3.11 -m py_compile $(find app tests alembic -name "*.py")
cd backend && black --check --quiet app tests alembic
cd backend && flake8 app tests alembic
cd backend && mypy --strict .
cd backend && TEST_DATABASE_URL="postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5433/ghost_sweep_test" TEST_REDIS_URL="redis://localhost:6379/1" pytest -v --cov=app --cov-report=term-missing --cov-fail-under=80
cd backend && bandit -r app
cd backend && pip-audit
```

Frontend verification:

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm audit --audit-level=high
```

Extension verification:

```bash
node extension/tests/smoke.test.mjs
```

Docker verification:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

## Contributing

Read `CONTRIBUTING.md`, `AGENTS.md`, and `CODE_OF_CONDUCT.md` before opening a pull request.

## License

MIT. See `LICENSE`.
