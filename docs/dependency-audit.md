# Dependency Audit Status

This document records known dependency advisories after Batch 6I triage (2026-06-30). Do not hide new failures; re-run audits after dependency changes.

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

Exit code: **1** (16 known vulnerabilities in 6 packages)

Backend dependency manager: **pyproject.toml** with pinned versions in `[project.dependencies]` and `[project.optional-dependencies.dev]`. No requirements.txt lockfile; Docker installs from pyproject.toml.

### Advisory table (pip)

| Package | Installed | Severity | Advisory ID | Direct/Transitive | Runtime/Dev | Reachability | Fix version | Fix class | Action |
| ------- | --------- | -------- | ----------- | ----------------- | ----------- | ------------ | ----------- | --------- | ------ |
| starlette | 0.41.3 | high | PYSEC-2026-161, PYSEC-2026-249, PYSEC-2026-248, GHSA-wqp7-x3pw-xc5r, GHSA-x746-7m8f-x49c | transitive via fastapi | **runtime** | production HTTP layer | 1.0.1–1.3.1 | **major** (0.x → 1.x) | **Deferred** — FastAPI 0.115.6 requires `starlette<0.42.0,>=0.40.0` |
| starlette | 0.41.3 | high | GHSA-2c2j-9gv5-cj73 | transitive via fastapi | runtime | multipart upload paths | 0.47.2 | patch (within 0.x) | **Deferred** — blocked by FastAPI starlette upper bound |
| starlette | 0.41.3 | high | GHSA-7f5h-v6xp-fcq8 | transitive via fastapi | runtime | FileResponse/static (not used in current API) | 0.49.1 | minor (within 0.x) | **Deferred** — blocked by FastAPI starlette upper bound; low immediate exposure |
| black | 24.10.0 | moderate | GHSA-3936-cmfr-pm3m | direct (dev) | dev-only | local formatter CLI | 26.3.1 | **major** (24 → 26) | **Deferred** — dev-only |
| pytest | 8.3.4 | high | GHSA-6w46-j5rx-g56g | direct (dev) | dev-only | local test runner | 9.0.3 | **major** (8 → 9) | **Deferred** — dev-only |
| pip | 25.1.1 | high | PYSEC-2026-196, GHSA-4xh5-x5gv-qwph, etc. | tooling (not in pyproject) | dev-only | local pip CLI | 26.1.2 | **major** | **Deferred** — host tooling, not app dependency |
| wheel | 0.45.1 | high | GHSA-8rrh-rw8j-w5fx | tooling (not in pyproject) | dev-only | wheel unpack CLI | 0.46.2 | patch | **Deferred** — host tooling |
| loguru | 0.5.3 | low | PYSEC-2022-14 | transitive | unknown/local-only | not used by app code directly | 0.5.3 listed / 0.7.3 available | patch | **Deferred** — transitive; not pinned in pyproject |

### pip future remediation plan

1. **Batch 7+ (requires explicit approval):** FastAPI/Starlette upgrade batch
   - Upgrade FastAPI to a release that supports Starlette 1.x (currently pinned at 0.115.6 with `starlette<0.42.0`)
   - Full backend pytest, mypy, bandit, and live E2E validation
2. **Optional dev batch:** pytest 9.x and black 26.x with test/format verification
3. **Future hardening:** consider pip-tools or uv lockfile for reproducible backend installs

## Remediated in Batch 6I

None. Triage-only batch; no safe patch/minor upgrades cleared high-severity runtime advisories.

## Prior remediation (pre-6I)

- `next@14.2.35` and `eslint-config-next@14.2.35` (from 14.2.21) — removed critical Next.js advisory class on 14.2.21 without jumping to Next 16

## Issue #4 status

**Issue #4 remains open.** Dependency advisories are documented with classification and deferred remediation plans. Do not close until either:

- Safe upgrades are applied and audits pass, or
- Remaining advisories are formally accepted with signed-off risk rationale for launch

## Re-check commands

```bash
cd frontend && npm audit --audit-level=high
cd frontend && npm audit fix --dry-run
cd backend && pip-audit
python3.11 scripts/live_e2e_validation.py --skip-public-mvp
```

CI runs pip-audit and npm audit with `continue-on-error: true` so advisories remain visible without blocking the gate until remediated or formally accepted. GitHub Actions is currently billing-blocked before job steps execute; local validation is source of truth.
