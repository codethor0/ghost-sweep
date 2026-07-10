# Contributing to ghost-sweep

Thank you for helping improve hiring transparency.

## Before you start

1. Read `README.md`, `AGENTS.md`, [GOVERNANCE.md](GOVERNANCE.md), and `docs/architecture.md`
2. First-time contributors should read [docs/contributor-onboarding.md](docs/contributor-onboarding.md)
3. Review [docs/reporting-and-moderation-policy.md](docs/reporting-and-moderation-policy.md) before working on intake or moderation-related areas
4. Search existing issues and pull requests; comment on or claim an issue before starting substantial work
5. Open a **draft pull request** early for substantial or uncertain work
6. Keep changes narrowly scoped and follow existing architecture and doctrine
7. Do not include private report data, Form responses, Sheet exports, or secrets in issues or pull requests
8. Wait for required CI and code-owner review before expecting merge

Use the GitHub issue templates under `.github/ISSUE_TEMPLATE/` when opening contributor tasks, bugs, or documentation work. See [docs/labels.md](docs/labels.md) for the live label taxonomy.

First pull requests should stay small: extend offline helpers and unit tests before touching API routes, schema, Docker, or CI.

## Safe contributor lanes

These lanes are suitable for community contributions with normal maintainer review:

- Documentation and contributor onboarding improvements
- Tests and local validation improvements
- Job URL validation helpers and fixtures (offline only)
- Accessibility improvements to the public MVP
- Public MVP usability improvements (no Form URL changes without approval)
- Duplicate-detection research and offline test fixtures
- Non-sensitive moderation UI planning documents (docs-only)
- Bug reproduction with minimal, scoped fixes
- Developer experience improvements that do not change sensitive paths

## Approval-required lanes

Stop and get **project-owner approval** before changing:

- Backend API routes or response contracts
- Authentication or authorization behavior
- Database schema or Alembic migrations
- Docker or CI workflow configuration
- Extension backend integration
- Public launch assets (`public-mvp/` Form URL, GitHub Pages, repository visibility)
- Privacy rules and public report publication behavior
- Sheet import scripts, `--apply`, or production data writes
- New dependencies (exact package, version, rationale, and alternatives)

Community review lead [@bgreg](https://github.com/bgreg) may approve and merge ordinary contributions in safe lanes after required checks pass. Sensitive paths in `.github/CODEOWNERS` require project-owner review from [@codethor0](https://github.com/codethor0).

Prefer **squash merging** for normal contributor pull requests.

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
python3.11 scripts/sync_public_mvp.py
python3 -m http.server 8080 --directory public-mvp
```

Extension API integration remains deferred. Evidence file upload and public backend hosting are deferred.

## Local verification

GitHub Actions CI is active and passing on `main`. Local verification is still required before every push and pull request.

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
python3.11 scripts/sync_public_mvp.py
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

All contributors must follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Report security issues through [SECURITY.md](SECURITY.md). Read [GOVERNANCE.md](GOVERNANCE.md) for maintainer roles and approval boundaries.
