# Dependency Audit Status

This document records known dependency advisories after Batch 7E triage (2026-06-30). Do not hide new failures; re-run audits after dependency changes.

## Batch 7E summary (triage — docs only)

| Item | Result |
| ---- | ------ |
| Audit date | 2026-06-30 |
| Starting commit | `a8e2906` (Batch 7D) |
| npm audit --audit-level=high | **PASS** (unchanged since Batch 7C) |
| npm audit (full) | **2 moderate** — PostCSS GHSA-qx2v-qp2m-jg93 only |
| pip-audit (full host scan) | **7 findings in 3 packages** — host-only noise |
| pip-audit (project-pinned) | **PASS** — no pyproject.toml advisories |
| Runtime advisories | **All cleared** (Starlette Batch 7B; npm high Batch 7C) |
| Project-pinned dev advisories | **All cleared** (black/pytest Batch 7D) |
| Issue #4 | **Ready to narrow/close** — see recommended update below |

Batch 7E is a triage-only checkpoint. No dependency manifest or application changes. Re-ran audits at `a8e2906` and classified all remaining findings as accepted deferred risk or local-environment noise.

### Remediation history (project scope)

| Batch | Scope | Result |
| ----- | ----- | ------ |
| 7B | Backend runtime (`fastapi==0.138.2`) | Starlette runtime advisories **cleared** |
| 7C | Frontend (`next@16.2.9`, ESLint 9) | npm **high** advisories **cleared** |
| 7D | Backend dev pins (`black`, `pytest`) | Project-pinned pip dev advisories **cleared** |
| 7E | Triage only | PostCSS moderate + host noise **documented as accepted** |

### Accepted deferred findings (post Batch 7E)

| Finding | Severity | Classification | Rationale | Revisit trigger |
| ------- | -------- | -------------- | --------- | --------------- |
| postcss GHSA-qx2v-qp2m-jg93 | moderate | **Accepted deferred** | Build-time Tailwind/PostCSS pipeline only; bundled in `next@16.2.9`; no safe fix without `npm audit fix --force` (downgrades next to 9.x) | `next` release bundles postcss >= 8.5.10 |
| host pip 25.1.1 | high | **Local-environment noise** | Not pinned in pyproject.toml; host Python installer tooling | Upgrade host pip to >= 26.1.2 on dev machines |
| host wheel 0.45.1 | high | **Local-environment noise** | Not pinned in pyproject.toml; host build tooling | Upgrade host wheel to >= 0.46.2 on dev machines |
| host loguru 0.5.3 via ciphey | low | **Local-environment noise** | Not a ghost-sweep dependency; pip-audit scans unrelated host site-packages | Use isolated venv; ignore or uninstall ciphey |

### Issue #4 recommended update

After Batch 7E docs land, Issue #4 should be updated to reflect:

1. **Remediated:** Starlette runtime (7B), npm high (7C), project-pinned pip dev (7D).
2. **Accepted deferred:** PostCSS moderate (build-time; monitor next releases).
3. **Out of repo scope:** host pip, wheel, loguru (local dev machine hygiene).
4. **Launch impact:** Public MVP uses static HTML/CSS with no npm dependencies; accepted PostCSS risk applies to local Docker frontend build only. Public launch is not blocked by remaining audit noise when classified as above.

Issue #4 may be **closed** after maintainer accepts the classification, or kept open as a low-priority monitor for PostCSS/next releases.

## Batch 7D summary

| Item | Result |
| ---- | ------ |
| Audit date | 2026-06-30 |
| Starting commit | `f14f630` (Batch 7C) |
| black | 24.10.0 → **26.3.1** |
| pytest | 8.3.4 → **9.0.3** |
| pytest-asyncio | 0.24.0 → **1.4.0** |
| pip-audit (project-pinned dev deps) | 9 vulnerabilities in 5 packages → **7 in 3 packages** |
| black/pytest advisories | **Cleared** |
| Host-only findings | loguru (via ciphey), pip, wheel — not pinned in pyproject.toml |
| npm audit --audit-level=high | **PASS** (unchanged from Batch 7C) |
| Issue #4 | **Remains open** (moderate npm PostCSS + host pip/wheel/loguru) |

Batch 7D upgraded pinned dev dependencies in `backend/pyproject.toml` only. Black 26 required cosmetic reformat of three files (one Alembic migration version file, two test modules); no migration logic or schema changes. No backend API/auth/schema, runtime dependencies, Docker, CI, frontend, extension, or public-mvp changes. Full backend and unchanged-project gates pass.

### Remaining pip advisories (post Batch 7D)

| Package | Installed | Severity | Advisory ID | Direct/Transitive | Runtime/Dev | Action |
| ------- | --------- | -------- | ----------- | ----------------- | ----------- | ------ |
| loguru | 0.5.3 | low | PYSEC-2022-14 | transitive via **host ciphey** | host-only | **Not project dependency** — pip-audit scans host site-packages |
| pip | 25.1.1 | high | multiple | host tooling | dev-only | **Documented** — upgrade host pip outside pyproject.toml |
| wheel | 0.45.1 | high | GHSA-8rrh-rw8j-w5fx | host tooling | dev-only | **Documented** — upgrade host wheel outside pyproject.toml |

## Batch 7C summary

| Item | Result |
| ---- | ------ |
| Audit date | 2026-06-30 |
| Starting commit | `6f724b4` (Batch 7B) |
| next | 14.2.35 → **16.2.9** |
| eslint-config-next | 14.2.35 → **16.2.9** |
| eslint | 8.57.1 → **9.39.1** |
| npm audit (all) | 5 vulnerabilities (1 moderate, 4 high) → **2 moderate only** |
| npm audit --audit-level=high | **PASS** — no high-severity findings |
| pip-audit | **FAIL** — 9 vulnerabilities in 5 packages (dev/tooling only; unchanged from Batch 7B) |
| Starlette runtime advisories | **Cleared** (Batch 7B) |
| Issue #4 | **Remains open** (moderate npm PostCSS advisories + dev/tooling pip advisories) |

Batch 7C upgraded `next@16.2.9`, `eslint-config-next@16.2.9`, and `eslint@9.39.1` in `frontend/package.json`. Migrated ESLint to flat config (`eslint.config.mjs`); lint script changed from `next lint` to `eslint .`. Migrated dynamic route pages to async `params` (Next 15+/16 requirement). No backend API/auth/schema, Alembic, Docker, CI, extension, or public-mvp changes. Full frontend gates and live E2E pass on Next.js 16 stack.

### Remaining npm advisories (post Batch 7C)

| Package | Installed | Severity | Advisory | Direct/Transitive | Runtime/Dev | Action |
| ------- | --------- | -------- | -------- | ----------------- | ----------- | ------ |
| postcss | 8.4.49 (direct); bundled in next | moderate | GHSA-qx2v-qp2m-jg93 | direct devDep + transitive in next | dev/build | **Deferred** — bundled postcss in next@16.2.9 still flagged; no safe patch without next canary or postcss major in next dependency tree |

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

Exit code: **0** (no high-severity findings; 2 moderate remain in full audit)

Full audit (`npm audit` without level filter): **2 moderate** — postcss bundled in next and direct devDep (GHSA-qx2v-qp2m-jg93). No safe fix without `npm audit fix --force` (would downgrade next to 9.x).

### Prior npm advisory table (pre Batch 7C, for reference)

| Package | Installed (was) | Severity | Status |
| ------- | --------------- | -------- | ------ |
| next | 14.2.35 | high | **Remediated Batch 7C** (16.2.9) |
| glob | 10.3.10 | high | **Remediated Batch 7C** (via eslint-config-next 16.2.9) |
| eslint-config-next | 14.2.35 | high | **Remediated Batch 7C** (16.2.9) |
| postcss | 8.4.49 | moderate | **Remains** — build-time only |

### npm accepted deferred (Batch 7E)

PostCSS GHSA-qx2v-qp2m-jg93 is **formally accepted deferred risk** as of Batch 7E:

- Reachability: build-time CSS pipeline only; not exposed in public MVP static site
- Fix path: requires `npm audit fix --force` which downgrades `next` to 9.x (breaking)
- Direct `postcss` patch does not clear audit because `next` bundles its own postcss copy
- `npm audit --audit-level=high` **passes**; only moderate severity remains

### npm future remediation plan

1. Monitor next releases for bundled postcss >= 8.5.10
2. Optional: bump direct `postcss` devDep when next dependency tree clears

## pip-audit summary

Command:

```bash
cd backend && pip-audit
```

Exit code: **1** (7 known vulnerabilities in 3 packages — host tooling + non-project loguru after Batch 7D)

Backend dependency manager: **pyproject.toml** with pinned versions in `[project.dependencies]` and `[project.optional-dependencies.dev]`. No requirements.txt lockfile; Docker installs from pyproject.toml.

### Remediated in Batch 7D (dev, pinned in pyproject.toml)

| Package | Before | After | Result |
| ------- | ------ | ----- | ------ |
| black | 24.10.0 | 26.3.1 | GHSA-3936-cmfr-pm3m **cleared** |
| pytest | 8.3.4 | 9.0.3 | GHSA-6w46-j5rx-g56g **cleared** |
| pytest-asyncio | 0.24.0 | 1.4.0 | Required for pytest 9 compatibility |

### Remaining pip advisories (post Batch 7D, project-pinned)

None. All pyproject.toml-pinned packages pass pip-audit when host contamination is excluded.

### Remaining pip advisories (full host scan, post Batch 7D)

| Package | Installed | Severity | Advisory ID | Direct/Transitive | Runtime/Dev | Action |
| ------- | --------- | -------- | ----------- | ----------------- | ----------- | ------ |
| loguru | 0.5.3 | low | PYSEC-2022-14 | host ciphey (not in pyproject) | host-only | **Not actionable in repo** |
| pip | 25.1.1 | high | multiple | host tooling | dev-only | Upgrade host pip to >= 26.1.2 |
| wheel | 0.45.1 | high | GHSA-8rrh-rw8j-w5fx | host tooling | dev-only | Upgrade host wheel to >= 0.46.2 |

### Prior remaining pip advisories (pre Batch 7D, for reference)

| Package | Installed (was) | Severity | Status |
| ------- | --------------- | -------- | ------ |
| black | 24.10.0 | moderate | **Remediated Batch 7D** (26.3.1) |
| pytest | 8.3.4 | high | **Remediated Batch 7D** (9.0.3) |

### Prior pip advisory table (pre Batch 7B, for reference)

Starlette runtime advisories listed below were **cleared** by FastAPI 0.138.2 upgrade:

| Package | Installed (was) | Severity | Advisory ID | Status |
| ------- | --------------- | -------- | ----------- | ------ |
| starlette | 0.41.3 | high | PYSEC-2026-161, PYSEC-2026-249, PYSEC-2026-248, GHSA-wqp7-x3pw-xc5r, GHSA-x746-7m8f-x49c, GHSA-2c2j-9gv5-cj73, GHSA-7f5h-v6xp-fcq8 | **Remediated Batch 7B** |

### pip future remediation plan

1. **Host tooling (outside repo):** upgrade host `pip` to >= 26.1.2 and `wheel` to >= 0.46.2 on developer machines
2. **Future hardening:** consider pip-tools or uv lockfile for reproducible backend installs; isolate dev venv from unrelated host packages (loguru/ciphey)

## Remediated in Batch 7D

- `black==26.3.1`, `pytest==9.0.3`, `pytest-asyncio==1.4.0` in pyproject.toml dev extras
- Clears all project-pinned pip-audit advisories (black, pytest)
- Validated: 154 pytest @ 84.34%, black --check, mypy, bandit; frontend/extension/public-mvp unchanged

## Remediated in Batch 7C

- `next@16.2.9`, `eslint-config-next@16.2.9`, `eslint@9.39.1` — clears all npm high advisories
- ESLint 9 flat config migration; dynamic route async `params` migration
- Validated: lint, typecheck, 25 Jest tests, build, live E2E (dynamic routes 200, report 201, vote 201)

## Remediated in Batch 7B

- `fastapi==0.138.2` (from 0.115.6) — clears all Starlette runtime advisories via transitive `starlette==1.3.1`
- Validated: 154 pytest @ 84.34%, mypy, bandit, live E2E (report 201, vote 201)

## Remediated in Batch 6I

None. Triage-only batch; no safe patch/minor upgrades cleared high-severity runtime advisories.

## Prior remediation (pre-6I)

- `next@14.2.35` and `eslint-config-next@14.2.35` (from 14.2.21) — removed critical Next.js advisory class on 14.2.21 without jumping to Next 16

## Issue #4 status

**Issue #4 ready for maintainer triage close (Batch 7E).** All project-scoped runtime and dev-tooling advisories are remediated or formally accepted:

| Category | Status |
| -------- | ------ |
| Backend runtime (Starlette) | **Remediated** (Batch 7B) |
| Frontend npm high | **Remediated** (Batch 7C) |
| Backend project-pinned dev | **Remediated** (Batch 7D) |
| PostCSS moderate (npm) | **Accepted deferred** — build-time; no safe non-force fix |
| Host pip/wheel/loguru | **Out of scope** — local-environment noise |

Full `npm audit` still reports 2 moderate PostCSS entries. Full host `pip-audit` still reports 7 entries in pip/wheel/loguru. These are documented accepted risk or environment noise, not project dependency failures.

Do not claim zero audit findings exist — claim that **project-scoped advisories requiring repo changes are resolved or accepted with rationale**.

## Re-check commands

```bash
cd frontend && npm audit --audit-level=high
cd frontend && npm audit fix --dry-run
cd backend && pip-audit
python3.11 scripts/live_e2e_validation.py --skip-public-mvp
```

CI runs pip-audit and npm audit with `continue-on-error: true` so advisories remain visible without blocking the gate until remediated or formally accepted. GitHub Actions is currently billing-blocked before job steps execute; local validation is source of truth.
