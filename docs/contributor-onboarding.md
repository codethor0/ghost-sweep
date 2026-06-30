# Contributor Onboarding

Onboarding guide for private collaborators on ghost-sweep. Read `CONTRIBUTING.md` and `AGENTS.md` first.

## Repository layout

| Path | Purpose |
| ---- | ------- |
| `public-mvp/` | Static GitHub Pages landing site (Google Form intake) |
| `backend/` | FastAPI API, services, tests |
| `frontend/` | Next.js app (local Docker) |
| `extension/` | MV3 scaffold (Batch 6D not started) |
| `docs/` | Architecture, API, launch plans |

Public MVP uses Google Form intake. The full database-backed app runs locally only until hosted infrastructure is approved.

## Local setup (Docker)

```bash
cp .env.example .env
docker compose up -d postgres postgres_test redis
docker compose up --build backend frontend
```

API: http://localhost:8000  
Frontend: http://localhost:3000

Optional demo data (development only):

```bash
cd backend
python3.11 scripts/seed_demo_data.py
```

## Backend verification

```bash
cd backend
python3.11 -m pip install -e ".[dev]"
python3.11 -m py_compile $(find app tests alembic -name "*.py")
black --check --quiet app tests alembic
flake8 app tests alembic
mypy --strict .
TEST_DATABASE_URL="postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5433/ghost_sweep_test" \
TEST_REDIS_URL="redis://localhost:6379/1" \
pytest -v --cov=app --cov-report=term-missing --cov-fail-under=80
bandit -r app
```

## Frontend verification

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm test
npm run build
```

## Public MVP validation

```bash
python3.11 scripts/validate_public_mvp.py
python3 -m http.server 8080 --directory public-mvp
```

## First contributor lane: job URL validation pipeline

See the GitHub issue titled **Contributor onboarding: job URL validation pipeline**.

Batch 6D adds an offline URL validation foundation in `backend/app/services/job_url_validation.py`. It does not scrape or call third-party sites. Future work can add controlled validation against company career pages only after policy and design review.

Scope summary:

- Pure Python helper module for URL normalization and ATS/platform detection
- Unit tests only; no network calls in the first PR
- No database schema changes in the first PR
- No backend API behavior changes unless separately approved
- No new dependencies without discussion

Platforms covered in tests: Workday, Greenhouse, Lever, Ashby, SmartRecruiters, generic company career pages, invalid URLs.

## Pull request expectations

Every PR must include:

- What changed and why
- How it was tested
- Security and privacy impact
- Rollback plan

Use draft PRs early. Keep scope small. Match existing code style (type hints, no emojis, no placeholders).

## Hygiene rules

- Do not commit `.env`, secrets, tokens, or validation logs with unredacted credentials
- Do not commit generated artifacts (`__pycache__`, `.pyc`, `node_modules`, `.next`, caches)
- Do not include AI or tool attribution in commits (no Co-authored-by from assistants)
- Redact tokens in any shared validation output; see `docs/validation-artifacts.md`

## What requires maintainer approval before you start

- Database schema changes or migrations
- Backend API or auth changes
- Docker or CI changes
- New dependencies
- Public launch changes (GitHub Pages, Form URL, repo visibility)

## Related documents

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [implementation-status.md](implementation-status.md)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [public-launch-checklist.md](public-launch-checklist.md)
