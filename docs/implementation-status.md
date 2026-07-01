# Implementation Status

Summary of implemented scope through Batch 10A. For API details see [api.md](api.md).

## Current state (live)

| Item | Status |
| ---- | ------ |
| Public repository | https://github.com/codethor0/ghost-sweep |
| GitHub Pages static MVP | https://codethor0.github.io/ghost-sweep/ |
| Google Form intake | https://forms.gle/PsjaYrbrCjAgZXjW8 |
| CI on `main` | Passing |
| Full app (FastAPI/Postgres/Redis/Next.js) | Local Docker only |
| Hosted backend, scoring DB, import, moderation UI, evidence upload, extension API | Deferred |

Open GitHub issues: **6** (#1, #4, #5, #6, #7, #8). Closed launch blockers: #2, #3.

See [post-launch-roadmap.md](post-launch-roadmap.md) and [audit-remediation-plan.md](audit-remediation-plan.md).

Historical batch notes below are retained for traceability. Lines describing pre-launch blockers reflect the state at each batch, not the current live status.

---

## Authentication

Refresh tokens are opaque strings stored in Redis by SHA-256 hash. The refresh endpoint returns a new access token but **does not rotate** the refresh token; the same refresh token string is returned until expiry or logout revokes it.

## Backend (Batch 6B complete)

- Auth: register, login, me, refresh, logout, rate limiting
- Company and job posting read APIs with score breakdowns
- Reports, votes, employer claims, moderation, employer responses
- Scoring recalculation, score snapshots, audit logging

## Job URL validation (Batch 6D foundation)

- Offline helper module: `backend/app/services/job_url_validation.py`
- Normalizes http/https job posting URLs and detects likely ATS or career-page providers
- Workday, Greenhouse, Lever, Ashby, SmartRecruiters, and generic company career paths
- No network calls, scraping, or third-party API usage
- Not wired to backend API routes yet
- Future work may add controlled validation against company career pages only after policy and design review

## Contributor readiness (Batch 6E complete)

- GitHub issue templates: contributor task, bug report, documentation task (`.github/ISSUE_TEMPLATE/*.yml`)
- Pull request template with scope, out-of-scope, risk level, and hygiene checklists (`.github/pull_request_template.md`)
- CODEOWNERS for maintainer review on high-risk paths (`.github/CODEOWNERS`)
- Label taxonomy live on GitHub (22 labels); documented in [labels.md](labels.md)
- Issue #1 labeled: `help wanted`, `good first issue`, `area:backend`, `batch-6e`
- CONTRIBUTING.md and [contributor-onboarding.md](contributor-onboarding.md) polished for first PR lanes and Issue #1
- No application behavior changes
- No backend, auth, schema, or API changes
- No Docker, CI, or dependency changes
- No public launch changes (Form URL placeholder, Pages off, repository private)

## Documentation sync and launch preflight (Batch 6F)

- Post-6E validation: labels, Issue #1 taxonomy, templates, and local gates verified
- Stale baseline references updated to `fee68e1` across README and launch docs
- GitHub tracking issues created: #2 Form/Pages launch, #3 CI billing, #4 dependency advisories, #5 URL validation API design
- Greg Write invite pending acceptance (`gmcguirk-contractor`); not Admin/Maintain
- Public launch remains blocked: Form URL placeholder, Pages off, repository private
- GitHub Actions billing-blocked before job steps; local validation is source of truth
- No application, schema, API, Docker, CI, or dependency changes

## Contributor handoff and launch preflight (Batch 6G)

- Post-6F checkpoint verified: labels, Issues #1-#5, templates, and local gates
- Issue #1 handoff comment posted: Batch 6D foundation on main; first PR extends offline helper/tests only
- Launch blocker preflight documented (Form URL, Pages, checklist, CI billing, dependency advisories)
- Greg Write invite still pending acceptance; not Admin/Maintain
- No application, schema, API, Docker, CI, or dependency changes

## Evidence hardening (Batch 6H)

- Added `scripts/live_e2e_validation.py` for corrected auth/report/vote/frontend/public-MVP proof
- Added `scripts/create_audit_bundle.py` with strict exclusions for AppleDouble, caches, secrets, archives
- `.env.example` header clarified; `.gitignore` hardened for audit artifact patterns
- Docs updated: exact API paths, expected status codes (report 201, vote 201), no overstated CI success
- Audit bundles must contain real evidence reports, not placeholder stubs
- No backend API/auth/schema, Docker, CI, frontend, or extension behavior changes
- No public launch changes

## Dependency advisory triage (Batch 6I)

- Fresh npm audit and pip-audit captured at commit `6c81064`; see [dependency-audit.md](dependency-audit.md)
- npm: 5 vulnerabilities (1 moderate, 4 high); all high fixes require Next.js 16 major upgrade
- pip: 16 vulnerabilities in 6 packages; runtime Starlette advisories blocked by FastAPI 0.115.6 upper bound
- No safe patch/minor remediation applied; dependency manifests unchanged
- Issue #4 remains open with documented classification and future upgrade plan
- No backend API/auth/schema, Docker, CI, frontend, or extension behavior changes

## Backend runtime dependency remediation (Batch 7B)

- Upgraded `fastapi==0.138.2` in `backend/pyproject.toml` (transitive `starlette==1.3.1`)
- Starlette runtime advisories cleared; pip-audit reduced from 16 to 9 (dev/tooling only)
- Backend gates pass: py_compile, black, flake8, mypy, 154 pytest @ 84.34%, bandit
- Live E2E pass: report 201, get 200, vote 201, auth lifecycle, moderation ACL, all frontend routes
- No backend API/auth/schema, Alembic, Docker config, CI, frontend, extension, or public-mvp changes
- Frontend Next.js 16 deferred to Batch 7C; Issue #4 remains open

## Frontend Next.js 16 migration (Batch 7C)

- Upgraded `next@16.2.9`, `eslint-config-next@16.2.9`, `eslint@9.39.1` in `frontend/package.json`
- ESLint 9 flat config (`eslint.config.mjs`); lint script `eslint .` (replaces removed `next lint`)
- Dynamic route async `params` migration: `/companies/[id]`, `/postings/[id]`, `/postings/[id]/report`
- Minimal lint fixes: `HomeHero` Link usage, `DashboardPanel` loading-state pattern
- Frontend gates pass: lint, typecheck, 25 Jest tests, build; npm high advisories cleared
- Live E2E pass on Next 16 Docker stack: dynamic routes 200, report 201, vote 201
- No backend API/auth/schema, Alembic, Docker config, CI, extension, or public-mvp changes
- Issue #4 remains open for moderate npm PostCSS + dev/tooling pip advisories

## Backend dev/tooling advisory remediation (Batch 7D)

- Upgraded dev pins in `backend/pyproject.toml`: `black==26.3.1`, `pytest==9.0.3`, `pytest-asyncio==1.4.0`
- Project-pinned pip-audit advisories cleared (black, pytest); host pip/wheel/loguru documented as out-of-scope
- Black 26 cosmetic reformat: `002_employer_claim_constraints.py`, `test_migrations.py`, `test_reports.py` (no logic changes)
- Backend gates pass: py_compile, black, flake8, mypy, 154 pytest @ 84.34%, bandit
- Frontend, extension, public-mvp, Docker, CI unchanged
- Issue #4 remains open for moderate npm PostCSS + host pip/wheel

## Dependency advisory triage and launch readiness (Batch 7E)

- Triage-only docs checkpoint at commit `a8e2906`; no application or dependency manifest changes
- Confirmed remediated: Starlette runtime (7B), npm high (7C), project-pinned pip dev (7D)
- PostCSS moderate (GHSA-qx2v-qp2m-jg93) classified as **accepted deferred** — build-time, no safe non-force fix
- Host pip/wheel/loguru classified as **local-environment noise** — not project dependencies
- Full local validation gates pass; CI still billing-blocked (Issue #3)
- Public launch still blocked by Form URL, Pages off, repo private — not by remaining audit classifications
- Issue #4 ready for maintainer update/close per [dependency-audit.md](dependency-audit.md) Batch 7E section

## Frontend (Batch 6C complete)

- API client for health, auth, companies, job postings, reports, and score endpoints
- Pages: register, login, dashboard, companies list, company detail, posting detail, report form
- Access tokens stored in React state only; cleared on refresh or sign out
- Refresh token handling is not wired in the frontend
- Session is intentionally lost on page refresh
- Home page health probe and extension `posting_url` handoff display

## Extension (scaffold)

- MV3 popup for Chrome and Firefox
- Reads active tab URL and opens frontend with `?posting_url=`
- No backend API calls; extension wiring deferred

## Local demo seed

- `backend/scripts/seed_demo_data.py` creates one demo company and job posting in development only (idempotent)

## Public MVP (static site)

- Canonical static site source in `public-mvp/` (HTML/CSS only; no build step)
- Root `index.html`, `styles.css`, and `.nojekyll` mirror `public-mvp/` for GitHub Pages (branch deploy supports `/` or `/docs` only)
- Live site: https://codethor0.github.io/ghost-sweep/
- Report intake via Google Form (`https://forms.gle/PsjaYrbrCjAgZXjW8`); manual review via Google Sheet
- GitHub Pages hosts static content only; no FastAPI, PostgreSQL, or Redis
- Full Next.js frontend remains server-mode for local Docker; not deployed to Pages
- Live public scoring database not hosted yet
- Validation: `python3.11 scripts/validate_public_mvp.py`

See [google-form-intake-spec.md](google-form-intake-spec.md) and [post-launch-roadmap.md](post-launch-roadmap.md).

## Public repo and Pages (Batch 9B)

- Repository visibility: public
- GitHub Pages: enabled from `main` / root (mirrors `public-mvp/`)
- No backend API/auth/schema, Docker, CI, frontend app, or extension behavior changes
- When updating the live MVP, edit `public-mvp/` and copy to repo root

## Post-launch docs sync (Batch 9C)

- Public MVP copy updated: live Pages URL, live Form intake, full app local Docker only
- Removed stale pre-launch blocker language from static MVP pages
- Launch checklist updated for completed go-live gates
- Remaining deferred: public backend hosting, live scoring database, extension API integration, frontend moderation UI, evidence upload, Google Sheet import automation
- Greg Write invite (`gmcguirk-contractor`) still pending acceptance
- Issue #4 dependency tracking: maintainer decision to close/update

## Post-launch roadmap (Batch 10A)

- Added [post-launch-roadmap.md](post-launch-roadmap.md): Sheet import planning, moderation workflow, extension API wiring plan, contributor lanes
- Issue tracker sync: close completed launch issues; open planning issues #6--#8
- No backend API/auth/schema, Docker, CI, frontend app, or extension behavior changes

## Audit remediation (Batch 10B)

- Public-facing doc drift corrected (Next.js 16.2.9, live launch status, CI active)
- Historical launch plan archived to [archive/free-public-launch-plan.md](archive/free-public-launch-plan.md)
- Public MVP copy softened; footer links added; batch jargon removed from static pages
- Added `scripts/sync_public_mvp.py` for root mirror safety
- Audit bundle script hardened (AppleDouble fail-fast, current launch state in reports)
- Evidence and verification URL fields reject non-http/https schemes (request validation only)
- Added [audit-remediation-plan.md](audit-remediation-plan.md) and [repository-security.md](repository-security.md)
- GitHub repository description and homepage metadata updated
- No database schema, Docker, CI workflow, or extension behavior changes

## Moderation SOP (Batch 10C)

- Added [moderation-sop.md](moderation-sop.md): Sheet review states, reviewer workflow, decline/spam/duplicate codes, evidence and email privacy rules, escalation, import-readiness, audit trail
- Updated [google-form-intake-spec.md](google-form-intake-spec.md), [moderation-model.md](moderation-model.md), [post-launch-roadmap.md](post-launch-roadmap.md)
- Issue #7: operational SOP complete; product moderation UI still deferred
- No backend API/auth/schema, Docker, CI, frontend app, or extension behavior changes

## Deferred

- Evidence file upload
- Public company and job posting write APIs
- Extension backend API integration (deferred)
- Job URL validation API wiring (deferred; offline helper exists from Batch 6D)
- Frontend moderation, employer, and admin UI
- Frontend refresh-token persistence
- Release hardening
- Public backend hosting
- Google Sheet to PostgreSQL import automation

See README current project status and [dependency-audit.md](dependency-audit.md).
