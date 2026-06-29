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

Committed baseline: `1230309` (Batch 6A employer claims on remote).

Batch 6B (moderation + employer responses) is implemented locally and uncommitted pending review.

**Implemented (Batch 6A, committed):**

- Employer claim submit, admin approve/reject, migration 002 constraints
- Audit logging for claim lifecycle events

**Implemented (Batch 6B, uncommitted):**

- Admin moderation queue and report verify/dismiss transitions
- Employer responses with auto-dispute from `pending` or `verified`
- Score recalculation and audit logs on moderation/response writes

**Implemented (Batches 1–5, committed):**

- Auth through Batch 4: register, login, `/me`, refresh, logout, and auth rate limiting
- Company and job posting read APIs with score breakdowns
- Report create/read/list, vote endpoint, scoring pipeline, score snapshots

**Scaffold (not wired to API):**

- Frontend: Next.js scaffold only
- Browser extension: present under `extension/`; not live-tested against the current API

**Deferred (not started):**

- Evidence file upload
- Company and job posting write APIs
- Frontend and extension integration
- Dependency audit advisories (documented deferred findings in dev/transitive tooling)

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
python -m py_compile $(find backend -name "*.py")
cd backend && black --check .
cd backend && flake8 .
cd backend && mypy --strict .
cd backend && pytest
cd backend && bandit -r app
cd backend && pip-audit
```

Frontend verification:

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm audit
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
