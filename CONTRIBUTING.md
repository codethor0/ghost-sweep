# Contributing to ghost-sweep

Thank you for helping improve hiring transparency.

## Before you start

1. Read `README.md`, `AGENTS.md`, and `docs/architecture.md`
2. First-time contributors should read [docs/contributor-onboarding.md](docs/contributor-onboarding.md)
3. Start with [Issue #1](https://github.com/codethor0/ghost-sweep/issues/1) or another scoped contributor lane
4. Search existing issues and pull requests
5. Open a **draft pull request** early for substantial or uncertain work

Use the GitHub issue templates under `.github/ISSUE_TEMPLATE/` when opening contributor tasks, bugs, or documentation work. See [docs/labels.md](docs/labels.md) for the live label taxonomy (22 labels; legacy defaults preserved).

First pull requests should stay small: extend offline helpers and unit tests before touching API routes, schema, Docker, or CI.

## Maintainer approval required before you start

Stop and get maintainer approval before changing:

- Backend API routes or response contracts
- Authentication or authorization behavior
- Database schema or Alembic migrations
- Docker or CI workflow configuration
- Extension backend integration
- Public launch assets (`public-mvp/` Form URL, GitHub Pages, repository visibility)
- New dependencies (exact package, version, rationale, and alternatives)

## Development setup

See `README.md` for local setup and verification commands.

## Public MVP vs full-stack development

ghost-sweep has two paths:

| Path | Location | Purpose |
| ---- | -------- | ------- |
| Public MVP | `public-mvp/` | Static GitHub Pages site; report intake via Google Form |
| Full application | `backend/`, `frontend/`, Docker Compose | Local API, database, and Next.js UI |

Contributors working on the API, scoring, auth, or Next.js pages should use the Docker stack. The public MVP is plain HTML/CSS with no build step. Do not convert the full Next.js app to static export without approval.

Public MVP validation:

```bash
python3.11 scripts/validate_public_mvp.py
python3 -m http.server 8080 --directory public-mvp
```

Extension API integration remains deferred. Evidence file upload and public backend hosting are deferred.

## Local verification

Local verification is the source of truth while GitHub Actions is billing-blocked. Run the gates relevant to your change before requesting review.

Backend:

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

Frontend:

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm test
npm run build
```

Public MVP (when touching `public-mvp/`):

```bash
python3.11 scripts/validate_public_mvp.py
python3 -m http.server 8080 --directory public-mvp
```

Extension smoke:

```bash
node extension/tests/smoke.test.mjs
```

## Log and artifact hygiene

- Do not commit `.env`, secrets, tokens, or validation logs with unredacted credentials
- Do not commit generated artifacts (`__pycache__`, `.pyc`, `node_modules`, `.next`, caches, build info files)
- Do not include tool attribution in commits, code, comments, or documentation
- Redact JWTs, refresh tokens, and API keys before pasting logs in issues or pull requests
- See [docs/validation-artifacts.md](docs/validation-artifacts.md)

## Pull request requirements

Keep pull requests **scoped and small**. Prefer multiple focused PRs over one large change.

Every pull request must include:

- What changed
- Why it changed
- How it was tested
- Security impact
- Data and privacy impact
- Screenshots for UI changes
- Rollback plan

## Code standards

- No placeholders, stubs, or TODO comments
- No emojis in code, comments, commits, documentation, or test names
- Backend functions require type hints; public functions require Google-style docstrings
- Frontend components require explicit Props interfaces and strict TypeScript
- All list endpoints must paginate
- All scoring changes must include tests and documentation updates

## Testing expectations

- Backend coverage target: 80 percent
- Frontend coverage target: 70 percent
- Do not skip tests unless an issue link and explanation are provided

## Dependency changes

Open an issue or pull request note that includes:

- Exact package name and version
- Why it is needed
- Security or maintenance risk
- Alternative options

## Signed commits

Signed commits are preferred.

## Community

All contributors must follow `CODE_OF_CONDUCT.md`.
