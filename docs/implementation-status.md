# Implementation Status

Summary of implemented scope through Batch 13E. For API details see [api.md](api.md).

## Current state (live)

| Item | Status |
| ---- | ------ |
| Public repository | https://github.com/codethor0/ghost-sweep |
| GitHub Pages static MVP | https://codethor0.github.io/ghost-sweep/ |
| Google Form intake | https://forms.gle/PsjaYrbrCjAgZXjW8 |
| CI on `main` | Passing (`837175d`; run `28668960634`) |
| GitHub Pages deploy | Green after Batch 13I rerun |
| PR #9 (URL validation tests) | Merged |
| Full app (FastAPI/Postgres/Redis/Next.js) | Local Docker only |
| Batch 12 MVP readiness (Section 18 offline gate) | **Closed** — ACCEPTED-MVP (Batch 12S) |
| Live Sheet export proof | **BLOCKED-LIVE** |
| `--apply` / production import | **Blocked** |
| Moderation UI | Scoped (Batch 13E); not implemented |
| Hosted backend, scoring DB, evidence upload, extension API | Deferred |

Open GitHub issues: **6** (#1, #4, #5, #6, #7, #8). Closed launch blockers: #2, #3.

See [post-launch-roadmap.md](post-launch-roadmap.md), [audit-remediation-plan.md](audit-remediation-plan.md), and [implementation-readiness-report.md](implementation-readiness-report.md).

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

## Sheet import design (Batch 10D)

- Added [sheet-import-design.md](sheet-import-design.md): Sheet-to-backend field mapping, eligibility rules, dedupe, URL validation, company/posting/report strategies, dry-run design, idempotency, audit logging, non-goals
- Cross-linked moderation SOP, Form intake spec, post-launch roadmap
- Issue #6: design complete; CLI import implementation deferred to Batch 12A
- No backend API/auth/schema, Docker, CI, frontend app, or extension behavior changes

## Implementation readiness (Batch 10E)

- Added [implementation-readiness-report.md](implementation-readiness-report.md): issue tracker review (#1, #4--#8), Batch 12A prerequisites, Sheet column alignment checklist, live MVP verification
- Updated post-launch-roadmap batch sequence (10E); fixed Track 1 column reference
- **Verdict:** Design-ready for 12A; not approval-ready until maintainer checklist signed and live Sheet columns verified
- No application code changes

## Sheet import dry-run CLI (Batch 12A)

- Added [sheet_import.py](../backend/app/services/sheet_import.py): offline eligibility checks and dry-run planning per [sheet-import-design.md](sheet-import-design.md)
- Added [scripts/sheet_import_dry_run.py](../scripts/sheet_import_dry_run.py): local/admin-only dry-run CLI (no database writes)
- Added [scripts/verify_sheet_columns.py](../scripts/verify_sheet_columns.py): CSV header verification for SOP columns
- Unit tests in `backend/tests/test_sheet_import.py`
- Sanitized fixture: [backend/tests/fixtures/sheet_import_sample.csv](../backend/tests/fixtures/sheet_import_sample.csv)
- `--apply` mode deferred to Batch 12B; no schema or API changes

## Sheet import apply mode design gate (Batch 12B)

- Added [sheet-import-apply-design.md](sheet-import-apply-design.md): `--apply` eligibility, transaction boundaries, idempotency via audit logs, entity create/match rules, audit events, dry-run parity, rollback, duplicate handling, test plan, approval gates
- Cross-linked parent [sheet-import-design.md](sheet-import-design.md) and post-launch roadmap
- **Verdict:** Design-ready for 12B implementation review; blocked until maintainer approval gates signed
- No application code, schema, API, Docker, CI, frontend, extension, or public MVP changes

## Audit remediation and gate cleanup (Batch 12C)

- Synced README current project status (removed stale baseline commit reference)
- Updated implementation-readiness-report, public-launch-checklist, post-launch-roadmap, repository-security, dependency-audit for 12A/12B shipped state
- Re-verified Sheet dry-run CLI, public MVP validator, and full local validation gates
- Issue #6 comment posted: 12A/12B complete; `--apply` pending section 18 approval
- **Verdict:** Docs and tracker aligned; `--apply` implementation remains blocked
- No application code, schema, API, Docker, CI, frontend, extension, or public MVP behavior changes

## Sheet import live verification blocker (Batch 12G)

Docs-only status update after Batch 12F-K. This is **not** final Section 18 sign-off.

### Google automation failure (Batch 12F)

All attempted live Google paths failed:

- Sheet grid editing
- Bound Apps Script (Page Not Found from linked Sheet)
- Standalone Apps Script paste/run (Monaco editor automation)
- clasp (authenticated to wrong Google account)
- Sheets API (unavailable)

No live post-upload CSV exists. No live Sheet export passed verification.

### Local fallback artifact (Batch 12F-K)

Fallback artifacts exist **outside the repo** and are **not** live Sheet exports:

- Raw: `/Users/thor/Downloads/ghost-sweep-sheet-exports/ghost-sweep-intake-local-fallback-export.csv`
- Sanitized: `/Users/thor/Downloads/ghost-sweep-sheet-exports/ghost-sweep-intake-local-fallback-sanitized.csv`

Artifact type: local sanitized fallback based on Batch 12F-H test row shape and SOP values.

The fallback artifact proves the importer accepts the intended 20-column shape and valid consent path, but it does not replace live Sheet verification.

### Verification summary (2026-07-02)

| Target | verify_sheet_columns.py | sheet_import_dry_run.py | processed | would_import | skipped |
| ------ | ----------------------- | ----------------------- | --------- | ------------ | ------- |
| Fixture (`backend/tests/fixtures/sheet_import_sample.csv`) | PASS | PASS | 2 | 1 | 1 |
| Fallback sanitized (outside repo) | PASS | PASS | 1 | 1 | 0 |

Fixture skip reason: row 3 `import_ready` must be yes (expected fixture behavior).

### Section 18 gate status

| Gate | Status |
| ---- | ------ |
| Gate 11 (live Sheet columns via `verify_sheet_columns.py`) | BLOCKED-LIVE / FALLBACK-PASS |
| Gate 12 (live dry-run via `sheet_import_dry_run.py`) | BLOCKED-LIVE / FALLBACK-PASS |
| Final Section 18 sign-off | Not ready |

Do not implement `--apply` until a real live Sheet export passes all Section 18 live gates or Section 18 is explicitly amended by maintainer decision.

### Required blocker before true Section 18 sign-off

A real live Sheet export with exact A:T headers and at least one valid import-ready row must pass:

1. `python3.11 scripts/verify_sheet_columns.py <export.csv>`
2. `python3.11 scripts/sheet_import_dry_run.py <export.csv>`

Recommended manual path: repair SOP columns L:T on the linked Sheet (row 3 only for moderation values; do not modify row 2), export CSV, verify with the commands above. Standalone Apps Script source prepared outside repo at `/Users/thor/Downloads/ghost-sweep-sheet-exports/ghost-sweep-sheet-repair-standalone.gs` (requires manual paste/run as `ghostsweep.community@gmail.com`).

- **Verdict:** Importer accepts correct 20-column shape and valid consent path (fallback proof). Live Gates 11 and 12 remain blocked until a real live Sheet export passes. Apply mode remains blocked.
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes

## Sheet import offline artifact verification (Batch 12F-P / docs Batch 12Q)

Docs-only checkpoint after Batch 12F-P. This is **OFFLINE-PASS only**, not live Google Sheet proof. **Not** final Section 18 sign-off.

Batch 12F-P completed offline artifact verification for the Sheet import post-upload shape. The generated offline CSV matched all 20 expected headers and dry-run accepted one importable row. This confirms the importer accepts the expected post-upload structure and moderation values.

However, this is not live Google Sheet proof. The live Sheet export remains blocked because Google Sheets / Apps Script export has not yet produced the required local CSV from the live Sheet.

### OFFLINE-PASS (Batch 12F-P)

- 20-column post-upload artifact verified (`verify_sheet_columns.py` PASS on sanitized export).
- Dry-run result: processed=2, would_import=1, skipped=1.
- Row 2 skip reason: `review_status` not `approved_for_import` (stale legacy row; expected).
- Row 3: WOULD_IMPORT with valid consent path and approved SOP fields.
- Notes redaction occurred in sanitized CSV (outside repo).
- Offline artifact paths (outside repo): raw and sanitized exports under `/Users/thor/Downloads/ghost-sweep-sheet-exports/ghost-sweep-intake-post-upload-export.csv` (generated from Batch 12F-O offline bundle, not a live Sheet download).

| Target | verify_sheet_columns.py | sheet_import_dry_run.py | processed | would_import | skipped |
| ------ | ----------------------- | ----------------------- | --------- | ------------ | ------- |
| Offline post-upload sanitized (outside repo) | PASS | PASS | 2 | 1 | 1 |

Offline artifact Gate 11: **READY**. Offline artifact Gate 12: **READY**.

### LIVE STATUS (unchanged)

- Gate 11 remains **BLOCKED-LIVE** until `verify_sheet_columns.py` passes on a live Google Sheet export.
- Gate 12 remains **BLOCKED-LIVE** until `sheet_import_dry_run.py` passes on a live Google Sheet export with at least one `would_import` row.
- Final Section 18 live sign-off: **Not ready**.

Do not implement `--apply` until explicitly approved in a later maintainer decision. See Batch 12S for Section 18 MVP amendment.

- **Verdict:** Importer path confirmed on offline post-upload artifact. Live Gates 11 and 12 remain blocked. Apply mode remains blocked.
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes during verification

## Section 18 gate amendment for MVP (Batch 12S)

Docs-only maintainer decision (2026-07-02). **Does not claim live Google Sheet proof passed.**

### Maintainer decision

For **MVP readiness only**, the maintainer accepts Batch 12F-P offline artifact verification as sufficient evidence that the importer accepts the expected 20-column post-upload Sheet shape and moderation values.

This decision **does not** represent live Google Sheet export proof. Google Sheets UI / Apps Script export remains an operational blocker.

### SECTION 18 AMENDED FOR MVP

- **Offline importer gate accepted** (Batch 12F-P: 20 headers, dry-run processed=2, would_import=1, skipped=1).
- **Live Google Sheet export proof deferred** — tracked separately as BLOCKED-LIVE.
- **Live proof remains required** before production Sheet import automation or `--apply` mode.
- **MVP readiness may proceed** under this amended Section 18 language for importer shape and dry-run behavior only.
- **`--apply` remains blocked** until a separate maintainer decision explicitly approves implementation (live export proof still required before production automation).

### Gate status after amendment

| Gate | Scope | Status |
| ---- | ----- | ------ |
| Offline Gate 11 (`verify_sheet_columns.py` on offline artifact) | MVP importer shape | **ACCEPTED-MVP** |
| Offline Gate 12 (`sheet_import_dry_run.py` on offline artifact) | MVP dry-run | **ACCEPTED-MVP** |
| Live Gate 11 (live Sheet export) | Production / live proof | **BLOCKED-LIVE** |
| Live Gate 12 (live Sheet dry-run) | Production / live proof | **BLOCKED-LIVE** |
| `--apply` implementation | Database writes | **Blocked** |

- **Verdict:** Section 18 amended for MVP readiness on offline verification only. Live Gates 11 and 12 remain BLOCKED-LIVE. Apply mode remains blocked.
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes

## Post–Batch-12 planning realignment (Batch 13B)

Docs-only checkpoint (2026-07-02). Aligns planning docs with Batch 12S/12T truth at commit `38a5589`.

- Batch 12 closed for MVP readiness under amended Section 18 offline gate language.
- Offline Gates 11/12: **ACCEPTED-MVP**. Live Gates 11/12: **BLOCKED-LIVE**.
- `--apply` and production import automation remain **blocked**.
- Next recommended execution batch: **13C** — public backend hosting spike (docs-only).
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes

## Public backend hosting readiness spike (Batch 13C)

Docs-only checkpoint (2026-07-02). No deploy performed.

- Added [hosting-readiness-spike.md](hosting-readiness-spike.md): runtime inventory, env/secrets checklist, Render/Fly/Railway comparison, Render recommended for MVP backend hosting.
- Full backend remains local Docker only; public MVP unchanged (Pages + Form + Sheet).
- Live Gates 11/12 remain **BLOCKED-LIVE**; `--apply` and production import remain **blocked**.
- Next recommended batch: **13D** — Render deployment plan (docs-only) or moderation UI scoping.
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes

## Render deployment plan (Batch 13D)

Docs-only checkpoint (2026-07-02). No deploy performed.

- Added [render-deployment-plan.md](render-deployment-plan.md): Render service layout, env matrix, secrets, migration strategy, security gates, staging/production checklists, rollback plan.
- Render recommended path from Batch 13C; **no Render resources created**.
- Live Gates 11/12 remain **BLOCKED-LIVE**; `--apply` and production import remain **blocked**.
- Next recommended batch: **13E** (moderation UI scoping or repository security settings plan) or **14A** staging implementation after explicit maintainer approval.
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes

## PR #9 merge and GitHub hygiene (Batch 13H / 13I)

- PR #9 squash-merged at `837175d`: regression tests for job URL normalization edge cases (tests-only; contributor bgreg).
- Main CI run `28668960634`: success on `837175d`.
- Pages run `28668960057`: failed on first deploy (transient GitHub Pages error); **green after rerun** (Batch 13I).
- Public MVP validator: PASS; live site HTTP 200.
- No application code changes by maintainer in 13H/13I.

## Moderation UI scoping (Batch 13E)

Docs-only checkpoint (2026-07-03). No UI implemented. No deploy performed.

- Added [moderation-ui-scope.md](moderation-ui-scope.md): product requirements, workflow, state model, UI screens, API assumptions, safety/privacy rules, decision rules, open questions, implementation boundaries.
- Documents gap between Sheet SOP fields and existing backend moderation APIs (`verify`/`dismiss` on `Report` only).
- Live Gates 11/12 remain **BLOCKED-LIVE**; `--apply` and production import remain **blocked**.
- Next recommended batch: **14B** — moderation API contract review (docs-only).
- No application code, schema, API, Docker, CI, frontend, extension, Google Form/Sheet, or public MVP changes

## Deferred

- Sheet import `--apply` mode (Batch 12B design shipped; implementation blocked)
- Evidence file upload
- Public company and job posting write APIs
- Extension backend API integration (deferred)
- Job URL validation API wiring (deferred; offline helper exists from Batch 6D)
- Frontend moderation, employer, and admin UI
- Frontend refresh-token persistence
- Release hardening
- Public backend hosting
- Google Sheet to PostgreSQL import `--apply` automation (dry-run CLI shipped)

See README current project status and [dependency-audit.md](dependency-audit.md).
