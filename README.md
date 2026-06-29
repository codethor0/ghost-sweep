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
  frontend/    Next.js web application
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
docker compose up -d postgres redis
docker compose up --build backend frontend
```

API: http://localhost:8000  
Frontend: http://localhost:3000

## Current project status

Latest pushed baseline: `682e349` (README Batch 6 status alignment; includes Batch 6B and CI workflow at `949b401`).

Batch 6A and Batch 6B are committed and pushed on `main`. Pre-6C remediation may exist locally and is not yet pushed. This is active development, not a release-ready product.

**CI:**

- GitHub Actions workflow is aligned with verified local backend gates (Python 3.11, postgres:15, redis:7, coverage ≥ 80%, advisory-only pip-audit for documented deferred advisories).
- GitHub Actions is currently blocked by account billing/spending limits, not by failing tests. Jobs do not start until billing is resolved.

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

**Scaffold (not wired to API):**

- Frontend: Next.js scaffold; health probe and extension `posting_url` display only
- Browser extension: popup links to frontend with posting URL query parameter; no backend API calls

**Deferred:**

- Evidence file upload
- Company and job posting write APIs
- Frontend wiring to the API
- Extension API integration
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
