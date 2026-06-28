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
