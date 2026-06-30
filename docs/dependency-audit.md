# Dependency Audit Status

This document records known dependency advisories after Batch 7B backend remediation (2026-06-30). Do not hide new failures; re-run audits after dependency changes.

## Batch 7B summary

| Item | Result |
| ---- | ------ |
| Audit date | 2026-06-30 |
| Starting commit | `f9bf756` (Batch 6I) |
| FastAPI | 0.115.6 → **0.138.2** |
| Starlette (transitive) | 0.41.3 → **1.3.1** |
| pip-audit | **FAIL** — 9 vulnerabilities in 5 packages (dev/tooling only) |
| Starlette runtime advisories | **Cleared** |
| npm audit --audit-level=high | **FAIL** — 5 vulnerabilities (unchanged; deferred to Batch 7C) |
| Issue #4 | **Remains open** (frontend npm + dev/tooling pip advisories) |

Batch 7B upgraded `fastapi==0.138.2` in `backend/pyproject.toml`. No backend app source, API, auth, schema, Docker, or CI changes. Full backend gates and live E2E pass on Next.js 14 frontend.

## Batch 6I summary

| Item | Result |
| ---- | ------ |
| Audit date | 2026-06-30 |
| Commit | `6c81064` (Batch 6H baseline; docs updated in Batch 6I) |
| npm audit --audit-level=high | **FAIL** — 5 vulnerabilities (1 moderate, 4 high) |
| pip-audit | **FAIL** — 16 vulnerabilities in 6 packages |
| Safe remediation applied | **None** — all npm high fixes require Next.js 16 major upgrade; pip runtime fixes require Starlette 1.x or FastAPI upgrade batch |
| Issue #4 | **Remains open** |

Batch 6I ran fresh audits, dry-run fix analysis, and classification. No dependency manifest changes were applied because no safe patch/minor fix clears high-severity runtime advisories without a major framework migration.

## npm audit summary

Command:

```bash
cd frontend && npm audit --audit-level=high
```

Exit code: **1** (5 vulnerabilities: 1 moderate, 4 high)

### Advisory table (npm)

| Package | Installed | Severity | Advisory | Direct/Transitive | Runtime/Dev | Reachability | Fix version | Fix class | Action |
| ------- | --------- | -------- | -------- | ----------------- | ----------- | ------------ | ----------- | --------- | ------ |
| next | 14.2.35 | high | GHSA-h25m-26qc-wcjf and related Next.js advisories | direct | runtime (local Docker frontend) | production runtime when frontend is deployed | 16.2.9 | **major** (Next 14 → 16) | **Deferred** — requires dedicated Next.js major upgrade batch with full frontend verification |
| glob | 10.3.10 | high | GHSA-5j98-mcp5-4vw2 | transitive via eslint-config-next | dev-only (lint CLI) | local-only during `npm run lint` | eslint-config-next@16.2.9 | **major** | **Deferred** — fix path requires eslint-config-next 16.x |
| eslint-config-next | 14.2.35 | high | via @next/eslint-plugin-next → glob | direct (devDep) | dev-only | local-only | 16.2.9 | **major** | **Deferred** |
| postcss | 8.4.49 (direct); bundled in next | moderate | GHSA-qx2v-qp2m-jg93 | direct devDep + transitive in next | dev/build (Tailwind/PostCSS pipeline) | build-time only | 8.5.16 (direct) or next@16.2.9 (bundled) | patch (direct) / **major** (via next) | **Deferred** — direct postcss patch to 8.5.16 does not clear audit because next bundles its own postcss |

### npm dry-run analysis

```bash
cd frontend && npm audit fix --dry-run
cd frontend && npm audit fix --package-lock-only --dry-run
```

Both commands report **no safe fixes**. All remediations require `npm audit fix --force`, which would install `next@16.2.9` and `eslint-config-next@16.2.9` (breaking major upgrades).

### npm future remediation plan

1. **Batch 7+ (requires explicit approval):** Next.js 14 → 16 major upgrade
   - Upgrade `next` and `eslint-config-next` together
   - Full frontend lint, typecheck, test, build, and live E2E validation
   - Review App Router, middleware, and image optimizer configuration for advisory-specific mitigations
2. Until then: local Docker frontend remains the validated runtime; public MVP is static HTML with no npm dependencies

## pip-audit summary

Command:

```bash
cd backend && pip-audit
```

Exit code: **1** (9 known vulnerabilities in 5 packages — dev/tooling only after Batch 7B)

Backend dependency manager: **pyproject.toml** with pinned versions in `[project.dependencies]` and `[project.optional-dependencies.dev]`. No requirements.txt lockfile; Docker installs from pyproject.toml.

### Remediated in Batch 7B (runtime)

| Package | Before | After | Result |
| ------- | ------ | ----- | ------ |
| fastapi | 0.115.6 | 0.138.2 | Upgraded in pyproject.toml |
| starlette | 0.41.3 | 1.3.1 (transitive) | All 7 runtime Starlette advisories **cleared** |

### Remaining pip advisories (post Batch 7B)

| Package | Installed | Severity | Advisory ID | Direct/Transitive | Runtime/Dev | Action |
| ------- | --------- | -------- | ----------- | ----------------- | ----------- | ------ |
| black | 24.10.0 | moderate | GHSA-3936-cmfr-pm3m | direct (dev) | dev-only | **Deferred** — requires black 26.x major |
| pytest | 8.3.4 | high | GHSA-6w46-j5rx-g56g | direct (dev) | dev-only | **Deferred** — requires pytest 9.x major |
| pip | 25.1.1 | high | multiple | tooling (not in pyproject) | dev-only | **Deferred** — host tooling |
| wheel | 0.45.1 | high | GHSA-8rrh-rw8j-w5fx | tooling (not in pyproject) | dev-only | **Deferred** — host tooling |
| loguru | 0.5.3 | low | PYSEC-2022-14 | transitive | unknown/local-only | **Deferred** — not pinned in pyproject |

### Prior pip advisory table (pre Batch 7B, for reference)

Starlette runtime advisories listed below were **cleared** by FastAPI 0.138.2 upgrade:

| Package | Installed (was) | Severity | Advisory ID | Status |
| ------- | --------------- | -------- | ----------- | ------ |
| starlette | 0.41.3 | high | PYSEC-2026-161, PYSEC-2026-249, PYSEC-2026-248, GHSA-wqp7-x3pw-xc5r, GHSA-x746-7m8f-x49c, GHSA-2c2j-9gv5-cj73, GHSA-7f5h-v6xp-fcq8 | **Remediated Batch 7B** |

### pip future remediation plan

1. **Batch 7C (requires explicit approval):** Next.js 14 → 16 major upgrade for frontend npm high advisories
2. **Optional dev batch:** pytest 9.x and black 26.x with test/format verification
3. **Future hardening:** consider pip-tools or uv lockfile for reproducible backend installs

## Remediated in Batch 7B

- `fastapi==0.138.2` (from 0.115.6) — clears all Starlette runtime advisories via transitive `starlette==1.3.1`
- Validated: 154 pytest @ 84.34%, mypy, bandit, live E2E (report 201, vote 201)

## Remediated in Batch 6I

None. Triage-only batch; no safe patch/minor upgrades cleared high-severity runtime advisories.

## Prior remediation (pre-6I)

- `next@14.2.35` and `eslint-config-next@14.2.35` (from 14.2.21) — removed critical Next.js advisory class on 14.2.21 without jumping to Next 16

## Issue #4 status

**Issue #4 remains open.** Backend Starlette runtime advisories are remediated. Remaining blockers:

- Frontend npm high advisories (Next.js 14 → 16, Batch 7C)
- Backend dev/tooling pip advisories (black, pytest, pip, wheel, loguru)

Do not close until frontend npm advisories are remediated or formally accepted, and remaining dev/tooling risk is documented or resolved.

Do not claim all dependencies are clean — npm audit still fails.

## Re-check commands

```bash
cd frontend && npm audit --audit-level=high
cd frontend && npm audit fix --dry-run
cd backend && pip-audit
python3.11 scripts/live_e2e_validation.py --skip-public-mvp
```

CI runs pip-audit and npm audit with `continue-on-error: true` so advisories remain visible without blocking the gate until remediated or formally accepted. GitHub Actions is currently billing-blocked before job steps execute; local validation is source of truth.
