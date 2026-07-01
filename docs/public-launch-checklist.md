# Public Launch Checklist

Complete this checklist before making the ghost-sweep repository public and enabling GitHub Pages.

## Launch readiness checkpoint (Batch 7E — 2026-06-30)

Commit baseline: `a8e2906`. Local validation is source of truth; GitHub Actions billing-blocked.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Backend runtime advisories | Cleared (Batch 7B) | No |
| Frontend npm high advisories | Cleared (Batch 7C) | No |
| Backend project-pinned dev advisories | Cleared (Batch 7D) | No |
| PostCSS moderate (npm) | Accepted deferred (Batch 7E) | No — build-time; public MVP has no npm |
| Host pip/wheel/loguru | Local-environment noise (Batch 7E) | No — not project deps |
| Full local backend/frontend gates | Pass | No |
| Extension smoke / public-mvp validator | Pass | No |
| Google Form URL | Placeholder | **Yes** |
| GitHub Pages | Not enabled | **Yes** (for public site) |
| Repository visibility | Private | **Yes** (for public repo) |
| GitHub Actions CI | Billing-blocked | **Yes** (Issue #3; local gates substitute) |
| Issue #4 dependency tracking | Ready to narrow/close | Maintainer decision |

**Public repo readiness:** Dependency advisories no longer block going public after maintainer accepts Batch 7E classification. Remaining blockers are Form URL, Pages configuration, repo visibility decision, and CI billing.

**Public site readiness:** Static `public-mvp/` is validated locally; Form URL replacement and Pages enable are required before public site launch.

## Repo hygiene

- [ ] All intended changes committed (docs, tests, public-mvp, scripts)
- [ ] No `.env` or secrets tracked in git
- [ ] No validation logs with unredacted tokens in the repo
- [ ] Generated caches removed (`__pycache__`, `.pyc`, `.DS_Store`, `._*`)
- [ ] `python3.11 scripts/validate_public_mvp.py` passes
- [ ] Full backend and frontend verification gates pass locally

## Authorship check

- [ ] `git config user.name` is Isaac Thor
- [ ] `git config user.email` is codethor@gmail.com
- [ ] `git config core.hooksPath` is `.githooks`
- [ ] Last 20 commits have no forbidden attribution strings (Co-authored-by, Cursor, AI assistant, etc.)
- [ ] All commits authored by Isaac Thor only

## Dependency audit status

- [x] Backend Starlette runtime advisories remediated (Batch 7B): `fastapi==0.138.2`, `starlette==1.3.1`
- [x] Backend `pip-audit` post-7B: 9 advisories in 5 packages (dev/tooling only); documented in [dependency-audit.md](dependency-audit.md)
- [x] Frontend npm high advisories remediated (Batch 7C): `next@16.2.9`, `eslint-config-next@16.2.9`, `eslint@9.39.1`; ESLint 9 flat config; async params migration
- [x] Frontend `npm audit --audit-level=high` passes (Batch 7C); 2 moderate PostCSS advisories remain (build-time)
- [x] Backend project-pinned dev advisories remediated (Batch 7D): `black==26.3.1`, `pytest==9.0.3`, `pytest-asyncio==1.4.0`
- [x] Backend `pip-audit` project-pinned dev deps clean; host pip/wheel/loguru documented as out-of-repo scope
- [x] PostCSS moderate advisory formally accepted as deferred risk (Batch 7E); build-time only; public MVP unaffected
- [x] Host pip/wheel/loguru classified as local-environment noise, not project dependencies (Batch 7E)
- [ ] Maintainer accepts Batch 7E classification and updates/closes Issue #4
- [ ] Host pip/wheel upgraded on developer machines (optional hygiene; not a repo blocker)

## GitHub Actions billing status

- [ ] Account billing/spending limits resolved OR documented as blocker
- [x] Local verification documented as source of truth if CI is blocked (see Issue #3)
- [x] Pages deploy plan does not require Actions if billing is blocked (use branch/folder publish)

## Google Form intake

- [ ] Google Form created per [google-form-intake-spec.md](google-form-intake-spec.md)
- [ ] Google Sheet linked to Form responses
- [ ] Sheet access restricted to maintainers
- [ ] Placeholder URL replaced in `public-mvp/index.html`
- [ ] Form privacy/moderation wording reviewed

## GitHub Pages

- [ ] `public-mvp/` contains `index.html`, `styles.css`, `.nojekyll`
- [ ] Local preview verified: `python3 -m http.server 8080 --directory public-mvp`
- [ ] Pages source configured: Settings -> Pages -> Deploy from branch -> main -> /public-mvp
- [ ] Site loads at project Pages URL after enable

## Documentation

- [x] [README.md](../README.md) updated with public MVP section
- [x] [CONTRIBUTING.md](../CONTRIBUTING.md) updated with MVP vs full-stack paths
- [x] [SECURITY.md](../SECURITY.md) updated with Form data handling
- [x] [implementation-status.md](implementation-status.md) updated
- [x] [free-public-launch-plan.md](free-public-launch-plan.md) reflects `public-mvp/` approach
- [x] [local-docker-validation.md](local-docker-validation.md) current

## Validation bundle

- [ ] Review bundle created with redacted logs
- [ ] No ANSI escape codes, emoji, AppleDouble, or `.DS_Store` in bundle
- [ ] No unredacted tokens in bundle
- [ ] `public-mvp/` included in bundle snapshot
- [ ] `.env.example` present and referenced by onboarding docs
- [ ] Live E2E script passes with report 201, report get 200, vote 201
- [ ] Audit bundles exclude AppleDouble (`._*`), `.DS_Store`, caches, and archives

## Human review

- [ ] Public MVP copy reviewed for accuracy and disclaimer clarity
- [ ] Privacy notes reviewed
- [ ] Google Form fields match spec
- [ ] No claim that full app is production-ready
- [ ] Maintainer agrees repo is public-contributor-ready

## Go public

- [ ] Repository visibility changed to public
- [ ] GitHub Pages enabled
- [ ] Form URL live and tested end-to-end
- [ ] Issue tracker and CONTRIBUTING link verified from public site

## Post-launch (deferred)

- [ ] Public backend hosting (Render, Fly, Railway, etc.)
- [ ] Live scoring database on public site
- [ ] Extension backend API integration (deferred; offline URL validation foundation exists from Batch 6D but is not API-wired)
- [ ] Evidence file upload
- [ ] Automated Google Sheet to PostgreSQL import
- [ ] Dependency advisory remediation batches

## Related documents

- [free-public-launch-plan.md](free-public-launch-plan.md)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [validation-artifacts.md](validation-artifacts.md)
- [dependency-audit.md](dependency-audit.md)
