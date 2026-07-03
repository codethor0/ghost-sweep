# Public Launch Checklist

Static public MVP launch status and remaining deferred work. Historical checkpoints below document pre-launch batches.

## Moderation UI wireframe spec (Batch 14C — 2026-07-03)

Docs-only. **No UI implemented.** No API implemented. No deploy performed.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Moderation UI wireframe spec | [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md) complete | No |
| Moderation UI implementation | Not started | No — deferred by design |
| Main CI on `a74603c` | Green (run `28670393922`) | No |
| Pages deploy | Green on `a74603c` | No |
| Live Gate 11 / 12 | BLOCKED-LIVE | Yes — unchanged |
| `--apply` / production import | Blocked | Yes — unchanged |

**Batch 14C:** Moderation UI wireframe/spec defined. No implementation. Live Sheet gates not reopened.

## Moderation API contract review (Batch 14B — 2026-07-03)

Docs-only. **No API implemented.** No UI implemented. No deploy performed.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Moderation API contract review | [moderation-api-contract-review.md](moderation-api-contract-review.md) complete | No |
| Moderation API implementation | Not started | No — deferred by design |
| Main CI on `7087897` | Green (run `28669761127`) | No |
| Pages deploy | Green on `7087897` | No |
| Live Gate 11 / 12 | BLOCKED-LIVE | Yes — unchanged |
| `--apply` / production import | Blocked | Yes — unchanged |

**Batch 14B:** Backend moderation contract mapped to Sheet SOP and UI scope. No API or behavior changes.

## Moderation UI scoping (Batch 13E — 2026-07-03)

Docs-only. **No UI implemented.** No deploy performed.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Moderation UI scope document | [moderation-ui-scope.md](moderation-ui-scope.md) complete | No |
| Moderation UI implementation | Not started | No — deferred by design |
| Main CI on `837175d` | Green (run `28668960634`) | No |
| PR #9 merged | Yes | No |
| Pages deploy | Green after Batch 13I rerun | No |
| Live Gate 11 / 12 | BLOCKED-LIVE | Yes — unchanged |
| `--apply` / production import | Blocked | Yes — unchanged |

**Batch 13E:** Moderation UI scoped for future implementation. Sheet + Form intake unchanged. Live Sheet gates not reopened.

## Launch readiness checkpoint (Batch 9C — 2026-07-01)

Commit baseline: `b4d397b`. Public static MVP is live.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Public MVP on GitHub Pages | Live at https://codethor0.github.io/ghost-sweep/ | No |
| Google Form intake | Live; manual Sheet review | No |
| Repository visibility | Public | No |
| Full app publicly hosted | No | No — intentional |
| Live public scoring database | Not hosted | Deferred |
| Public backend hosting | Not deployed | Deferred |
| Extension backend API integration | Not wired | Deferred |
| Frontend moderation / employer / admin UI | Wireframe spec (14C); not built | Deferred — see [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md) |
| Evidence file upload | Deferred | Deferred |
| Greg Write invite (`gmcguirk-contractor`) | Pending acceptance | Operational |
| Issue #4 dependency tracking | Open | Maintainer decision |

**Public MVP launch:** Complete (Batches G1A, 8A, 9B, 9C).

**Remaining product work:** Hosted backend, scoring database, extension integration, moderation UI, evidence upload. Sheet import dry-run and offline MVP gate complete (12A, 12F-P, 12S); `--apply` and production import **blocked**; live Sheet proof **BLOCKED-LIVE**.

## Sheet import verification status (Batch 12S — Section 18 MVP amendment — 2026-07-02)

Docs-only maintainer decision. **Does not claim live Google Sheet proof passed.**

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Sheet import dry-run CLI (12A) | Shipped | No |
| Sheet import apply design (12B) | Shipped | No |
| Offline Gate 11 (MVP, Batch 12F-P) | ACCEPTED-MVP | No |
| Offline Gate 12 (MVP, Batch 12F-P) | ACCEPTED-MVP | No |
| Live Gate 11: live Sheet columns | BLOCKED-LIVE | Yes — live export deferred |
| Live Gate 12: live dry-run on live export | BLOCKED-LIVE | Yes — live export deferred |
| Section 18 MVP readiness (offline) | Amended and accepted | No |
| Section 18 live sign-off | Not ready | Yes — required before production automation |
| `--apply` implementation | Blocked | Yes |

**SECTION 18 AMENDED FOR MVP:** Maintainer accepts Batch 12F-P offline verification (20 headers; processed=2, would_import=1, skipped=1) as sufficient for MVP importer readiness. Live Google Sheet export remains a known operational blocker. Live proof remains required before production automation or `--apply` mode.

Do not implement `--apply` until explicitly approved in a later maintainer decision.

See [implementation-status.md](implementation-status.md) Batch 12G, Batch 12F-P, and Batch 12S, and [sheet-import-apply-design.md](sheet-import-apply-design.md) section 18.

Historical offline verification checkpoint (Batch 12Q): see [implementation-status.md](implementation-status.md) Sheet import offline artifact verification section.

## Launch readiness checkpoint (Batch 9B — 2026-07-01)

Commit baseline: `95fd21e` (pre-9B-fix). Local validation is source of truth.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Google Form + Sheet | Complete (G1A) | No |
| public-mvp Form URL | Replaced (8A) | No |
| Manual Form -> Sheet test | Confirmed | No |
| Repository visibility | Public (9B) | No |
| GitHub Pages | Enabled from `main` / root | No (after root mirror fix) |
| Live MVP at Pages URL | Live (9B-fix) | No |
| Full app publicly hosted | No | No — intentional |

**Note:** GitHub Pages branch deploy supports `/` or `/docs` only. Root `index.html` mirrors `public-mvp/` for publishing; `public-mvp/` remains the canonical source.

## Launch readiness checkpoint (Batch 8A — 2026-06-30)

Commit baseline: `b4018b7` (pre-8A). Local validation is source of truth.

| Gate | Status | Blocker? |
| ---- | ------ | -------- |
| Backend runtime advisories | Cleared (Batch 7B) | No |
| Frontend npm high advisories | Cleared (Batch 7C) | No |
| Backend project-pinned dev advisories | Cleared (Batch 7D) | No |
| PostCSS moderate (npm) | Accepted deferred (Batch 7E) | No — build-time; public MVP has no npm |
| Host pip/wheel/loguru | Local-environment noise (Batch 7E) | No — not project deps |
| Full local backend/frontend gates | Pass (re-run in 8A) | No |
| Extension smoke / public-mvp validator | Pass (re-run in 8A) | No |
| Google Form | Created (Batch G1A) | No |
| Google Sheet | Linked (Batch G1A) | No |
| public-mvp Form URL | Replaced (Batch 8A) | No |
| Final post-fix Form submission test | PARTIAL — form loads at public URL; automated submit blocked; manual Sheet verify recommended | No |
| GitHub Pages | Not enabled | **Yes** (for public site) |
| Repository visibility | Private | **Yes** (for public repo) |
| GitHub Actions CI | Monitor ongoing | No at `b4018b7` |
| Issue #4 dependency tracking | Ready to narrow/close | Maintainer decision |

**Public repo readiness:** Form URL replaced in repo; Google Form and Sheet exist on project account. Remaining blockers are Pages configuration, repo visibility decision, and maintainer sign-off.

**Public site readiness:** Static `public-mvp/` validated locally with real Form URL; Pages enable and public launch not performed.

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

- [x] Google Form created per [google-form-intake-spec.md](google-form-intake-spec.md) (Batch G1A)
- [x] Google Sheet linked to Form responses (Batch G1A)
- [x] Sheet access restricted to project account (Batch G1A)
- [x] Placeholder URL replaced in `public-mvp/index.html` (Batch 8A)
- [x] Form privacy/moderation wording reviewed (Batch G1A)
- [x] End-to-end Form submission verified in linked Sheet (manual test confirmed)

## GitHub Pages

- [x] `public-mvp/` contains `index.html`, `styles.css`, `.nojekyll`
- [x] Root mirror: `index.html`, `styles.css`, `.nojekyll` (Batch 9B-fix; Pages branch deploy supports `/` or `/docs` only)
- [x] Local preview verified: `python3 -m http.server 8080 --directory public-mvp`
- [x] Pages source configured: Settings -> Pages -> Deploy from branch -> main -> `/` (root)
- [x] Site loads public MVP at https://codethor0.github.io/ghost-sweep/

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

- [x] Repository visibility changed to public (Batch 9B)
- [x] GitHub Pages enabled (Batch 9B; root mirror of `public-mvp/`)
- [x] Form URL live and tested end-to-end
- [x] Issue tracker and CONTRIBUTING link verified from public site

## Post-launch (deferred)

- [ ] Public backend hosting (Render — see [hosting-readiness-spike.md](hosting-readiness-spike.md) and [render-deployment-plan.md](render-deployment-plan.md); no deploy in Batch 13D)
- [ ] Live scoring database on public site
- [ ] Extension backend API integration (deferred; offline URL validation foundation exists from Batch 6D but is not API-wired)
- [ ] Evidence file upload
- [ ] Automated Google Sheet to PostgreSQL import
- [ ] Dependency advisory remediation batches

## Related documents

- [post-launch-roadmap.md](post-launch-roadmap.md)
- [hosting-readiness-spike.md](hosting-readiness-spike.md)
- [render-deployment-plan.md](render-deployment-plan.md)
- [moderation-ui-scope.md](moderation-ui-scope.md)
- [moderation-api-contract-review.md](moderation-api-contract-review.md)
- [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md)
- [free-public-launch-plan.md](free-public-launch-plan.md)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [validation-artifacts.md](validation-artifacts.md)
- [dependency-audit.md](dependency-audit.md)
