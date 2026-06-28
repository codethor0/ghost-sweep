# ghost-sweep

ghost-sweep is an open-source Job Integrity Database that helps job seekers evaluate hiring transparency using evidence-based reports, transparent risk signals, and employer response workflows.

## What this project does

- Collects structured, evidence-backed reports about job postings
- Tracks companies and posting history over time
- Calculates transparent ghost job risk signals with documented inputs and weights
- Provides employer claim, response, verification, and dispute pathways
- Offers a web application and browser extension entry points for reporting

## What this project does not do

- It does not make unsupported accusations or legal findings
- It does not publish private personal information
- It does not replace background checks, legal review, or direct employer communication
- It does not guarantee hiring outcomes or company intent

## Repository layout

```text
backend/     FastAPI API, scoring engine, auth, migrations
frontend/    Next.js web application
extension/   Chrome and Firefox Manifest V3 extensions
docs/        Architecture, API, scoring, moderation, legal guidance
```

## Requirements

- Python 3.11
- Node.js 20+
- Docker and Docker Compose
- PostgreSQL 15
- Redis 7

## Local development

1. Copy environment template:

```bash
cp .env.example .env
```

2. Start infrastructure and services:

```bash
docker compose up -d postgres redis postgres_test
docker compose up --build backend frontend
```

3. Run database migrations manually when working outside Docker:

```bash
cd backend
pip install ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

4. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

## Verification

Backend:

```bash
python -m py_compile $(find backend -name "*.py")
cd backend && black --check .
cd backend && flake8 .
cd backend && mypy --strict .
cd backend && pytest
cd backend && bandit -r app
cd backend && pip-audit
```

Frontend:

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm test
cd frontend && npm audit
```

Docker:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
```

## API overview

- `GET /health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/companies`
- `POST /api/v1/reports`
- `GET /api/v1/job-postings/{id}`
- `GET /api/v1/job-postings/{id}/risk-score`

See `docs/api.md` for details.

## Contributing

Read `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `AGENTS.md` before opening a pull request.

## Security

Report vulnerabilities using `SECURITY.md`.

## License

MIT
