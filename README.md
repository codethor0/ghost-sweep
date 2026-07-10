# Ghost Sweep

<p align="center">
  <img src="docs/assets/ghost-sweep-logo.svg" alt="Ghost Sweep logo" width="72" height="72" />
</p>

<p align="center">
  <strong>Community-maintained open-source project for reporting and reviewing suspected ghost job postings.</strong>
</p>

<p align="center">
  <a href="https://github.com/codethor0/ghost-sweep/actions/workflows/ci.yml"><img src="https://github.com/codethor0/ghost-sweep/actions/workflows/ci.yml/badge.svg" alt="CI status" /></a>
  <a href="https://codethor0.github.io/ghost-sweep/"><img src="https://img.shields.io/website?url=https%3A%2F%2Fcodethor0.github.io%2Fghost-sweep%2F&label=GitHub%20Pages" alt="GitHub Pages status" /></a>
  <img src="https://img.shields.io/github/license/codethor0/ghost-sweep" alt="MIT License" />
  <img src="https://img.shields.io/badge/status-active%20development-blue" alt="Active development" />
  <img src="https://img.shields.io/badge/contributions-welcome-green" alt="Contributions welcome" />
</p>

<p align="center">
  <a href="https://codethor0.github.io/ghost-sweep/">Public site</a> |
  <a href="https://forms.gle/PsjaYrbrCjAgZXjW8">Report a suspected ghost job</a> |
  <a href="https://github.com/codethor0/ghost-sweep/issues/15">Community roadmap</a>
</p>

Ghost Sweep helps job seekers submit **good-faith reports** about **suspected ghost job postings**. Community reports are **unverified allegations** until moderation is complete. The project protects personal information and does not present allegations as established facts.

**Status:** Active development public MVP. Not production-complete. Volunteer-maintained; no paid contributor roles.

| Link | URL |
| ---- | --- |
| Public site | https://codethor0.github.io/ghost-sweep/ |
| Report form | https://forms.gle/PsjaYrbrCjAgZXjW8 |
| Repository | https://github.com/codethor0/ghost-sweep |

## What Ghost Sweep does

- Provides a public landing page and Google Form for suspected ghost job reports
- Requires human moderation before reports are treated as credible
- Maintains open-source code for future integrity scoring, moderation UI, and local Docker development
- Documents privacy boundaries between public code and private submission data

## What Ghost Sweep does not do

- Does not publicly host the full backend API today
- Does not automatically verify or publish allegations
- Does not expose raw Form or Sheet submission data in the repository
- Does not run production Sheet import or `--apply`
- Does not promise paid roles or production readiness

See [docs/reporting-and-moderation-policy.md](docs/reporting-and-moderation-policy.md).

## Current public MVP flow

```mermaid
flowchart LR
    A[Job seeker] --> B[GitHub Pages public site]
    B --> C[Google Form]
    C --> D[Private Google Sheet]
    D --> E[Manual moderation]
    E --> F[Future reviewed workflow]
```

## Contribution workflow

```mermaid
flowchart LR
    A[Contributor selects issue] --> B[Creates branch or fork]
    B --> C[Opens draft pull request]
    C --> D[CI checks]
    D --> E[Maintainer review]
    E --> F[Protected merge to main]
```

Maintainers: [@codethor0](https://github.com/codethor0) (owner), [@bgreg](https://github.com/bgreg) (community review lead).

## How to contribute

1. Read [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), and [docs/contributor-onboarding.md](docs/contributor-onboarding.md)
2. Start with [Issue #15: Community contribution roadmap](https://github.com/codethor0/ghost-sweep/issues/15)
3. Comment on an issue before substantial work
4. Open a draft pull request early
5. Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [SECURITY.md](SECURITY.md)

Safe lanes: documentation, tests, job URL validation, accessibility, public MVP usability. Approval required for auth, schema, deploy, CI permissions, Sheet import, and `--apply`.

## Problem

Job seekers often invest time in postings that remain open without hiring intent, receive no recruiter follow-up, or are reposted repeatedly without closure. Hiring transparency is uneven, and public information is fragmented across boards, employer sites, and anecdotal reports.

## Solution

ghost-sweep collects structured, evidence-backed reports about job postings and companies, calculates documented integrity scores, and gives employers a path to verify active roles, respond to reports, and dispute incorrect information.

The platform uses risk-signal language. It does not make unsupported legal accusations.

## Architecture boundary

```mermaid
flowchart TB
    subgraph public [Public today]
        P[GitHub Pages]
        F[Google Form]
    end
    subgraph private [Private today]
        S[Google Sheet moderation]
    end
    subgraph local [Local Docker only]
        B[FastAPI backend]
        DB[(PostgreSQL)]
        R[(Redis)]
    end
    P --> F
    F --> S
    B --- DB
    B --- R
    S -.->|import blocked| B
```

| Layer | Hosting | Status |
| ----- | ------- | ------ |
| Public landing + report CTA | GitHub Pages | Live |
| Report intake | Google Form | Live |
| Moderation queue | Google Sheet | Private; manual |
| Full app | Local Docker | Not publicly hosted |
| Production import | Not enabled | `--apply` blocked; Live Gates 11/12 BLOCKED-LIVE |

```text
ghost-sweep/
  backend/     FastAPI API, scoring engine, auth, moderation services
  frontend/    Next.js web application (local Docker; server-mode)
  public-mvp/  Canonical static MVP source (mirrored to repo root for GitHub Pages)
  extension/   Manifest V3 browser extension for job board overlays
  docs/        Architecture, API, scoring, moderation, legal guidance
  .github/     CI workflows and community templates
```

Data stores:

- PostgreSQL 15 for primary records
- Redis 7 for auth rate limiting and refresh token storage

## Tech stack

Backend: Python 3.11, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2, PostgreSQL 15, Redis 7

Frontend: Next.js 16.2.9, React, TypeScript strict mode, Tailwind CSS

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

The free public launch path uses a standalone static site. Source files live in `public-mvp/`; root `index.html`, `styles.css`, and `.nojekyll` mirror that folder for GitHub Pages (branch deploy supports `/` or `/docs` only).

After editing `public-mvp/`, sync the root mirror:

```bash
python3.11 scripts/sync_public_mvp.py
python3.11 scripts/validate_public_mvp.py
```

| Layer | Hosting | Status |
| ----- | ------- | ------ |
| Public landing + report CTA | GitHub Pages (root mirror of `public-mvp/`) | Live at https://codethor0.github.io/ghost-sweep/ |
| Report intake | Google Form -> Google Sheet | Live; manual review per [moderation-sop.md](docs/moderation-sop.md) |
| Full app (FastAPI/Postgres/Redis) | Local Docker only | Not publicly hosted |
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

See [docs/google-form-intake-spec.md](docs/google-form-intake-spec.md), [docs/public-launch-checklist.md](docs/public-launch-checklist.md), [docs/post-launch-roadmap.md](docs/post-launch-roadmap.md), and [docs/sheet-import-design.md](docs/sheet-import-design.md).

The Google Form URL is `https://forms.gle/PsjaYrbrCjAgZXjW8`. Raw applicant emails must not be published.

## Current project status

Current `main` includes public launch (Batches 8A--10E), Sheet import dry-run (Batch 12A), apply-mode design (Batch 12B), offline verification (Batch 12F-P), Section 18 MVP amendment (Batch 12S), and moderation planning docs (Batches 13E--14E). The public static MVP and Google Form intake are live; the full application remains local Docker only.

**Live public surfaces:**

- **Repository:** public — https://github.com/codethor0/ghost-sweep
- **GitHub Pages MVP:** https://codethor0.github.io/ghost-sweep/
- **Google Form intake:** https://forms.gle/PsjaYrbrCjAgZXjW8
- **Google Sheet moderation:** manual review per [moderation-sop.md](docs/moderation-sop.md)

**Privacy and moderation:**

- Form and Sheet submission data remain private and are not published in the repository
- Reports require moderation before being treated as credible
- See [docs/reporting-and-moderation-policy.md](docs/reporting-and-moderation-policy.md)

**Sheet import pipeline:**

- **Batch 12A (shipped):** dry-run CLI — `scripts/sheet_import_dry_run.py`, `scripts/verify_sheet_columns.py`; no database writes
- **Batch 12B (shipped):** apply-mode design — [sheet-import-apply-design.md](docs/sheet-import-apply-design.md)
- **Batch 12F-P / 12S (shipped):** offline post-upload artifact verification **ACCEPTED-MVP**
- **Live Sheet export proof:** **BLOCKED-LIVE**
- **`--apply` implementation:** not implemented; blocked
- **Production import automation:** not enabled

**Current limitations:**

- No publicly hosted backend or live scoring database
- No public moderation UI (planning docs exist; implementation deferred)
- No production Sheet import automation
- Extension has no backend API integration yet
- Volunteer project; no guaranteed staffing or paid roles

**CI:**

- GitHub Actions CI passes on latest `main` (backend, frontend, extension smoke, public-mvp validator).
- Local verification remains required before every push and pull request.

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

**Contributor readiness:**

- GitHub issue templates, PR template, CODEOWNERS, and label taxonomy documented in [docs/labels.md](docs/labels.md)
- Community governance: [GOVERNANCE.md](GOVERNANCE.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md)
- Maintainer review lead: [@bgreg](https://github.com/bgreg) (Admin)
- Project owner: [@codethor0](https://github.com/codethor0)

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

**Deferred (not publicly hosted):**

- Public backend hosting and live scoring database
- Sheet import `--apply` mode (design complete; implementation blocked; live export proof required before production automation)
- Google Sheet to backend import automation (dry-run only; offline gate ACCEPTED-MVP; production import deferred)
- Public moderation UI and evidence file upload
- Extension backend API integration
- Wiring job URL validation into public API or intake flows
- Frontend moderation, employer, and admin UI
- Frontend refresh-token handling
- Remaining dependency advisories (see [docs/dependency-audit.md](docs/dependency-audit.md); Issue #4)

GitHub repository: https://github.com/codethor0/ghost-sweep (public)

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

Read [CONTRIBUTING.md](CONTRIBUTING.md), [GOVERNANCE.md](GOVERNANCE.md), [AGENTS.md](AGENTS.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before opening a pull request.

- [Community roadmap (Issue #15)](https://github.com/codethor0/ghost-sweep/issues/15)
- [Support and community help](SUPPORT.md)
- [Security policy](SECURITY.md)
- [Reporting and moderation policy](docs/reporting-and-moderation-policy.md)
- [Contributor onboarding](docs/contributor-onboarding.md)
- [Changelog](CHANGELOG.md)

## License

MIT. See [LICENSE](LICENSE).
