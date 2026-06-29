# Dependency Audit Status

This document records known dependency advisories that remain after the smallest safe upgrades applied during pre-6C remediation. Do not hide new failures; re-run audits after dependency changes.

## Summary

| Audit | Exit code at checkpoint | Runtime risk | Dev/tooling risk |
| ----- | ----------------------- | ------------ | ---------------- |
| pip-audit | 1 | Starlette (via FastAPI) | black, pytest, pip, wheel, loguru |
| npm audit --audit-level=high | 1 | Next.js 14.x runtime | glob via eslint-config-next (lint CLI only) |

## Backend: pip-audit

Command:

```bash
cd backend && pip-audit
```

Status: **16 known vulnerabilities in 6 packages** (dev and transitive tooling).

### Runtime advisories (deferred temporarily)

| Package | Role | Status |
| ------- | ---- | ------ |
| starlette | Transitive via FastAPI; serves HTTP requests | **Deferred temporarily.** Remediation likely requires FastAPI/Starlette upgrade batch with full regression testing. Accepted for local development until a dedicated dependency batch. |

### Dev and tooling advisories (lower runtime exposure)

| Package | Role | Status |
| ------- | ---- | ------ |
| black | Dev formatter | Deferred; dev-only |
| pytest | Dev test runner | Deferred; dev-only |
| pip | Tooling | Deferred; dev-only |
| wheel | Tooling | Deferred; dev-only |
| loguru | Transitive | Deferred; review in dependency batch |

CI runs pip-audit with `continue-on-error: true` so advisories remain visible without blocking the gate until remediated or formally accepted.

## Frontend: npm audit

Command:

```bash
cd frontend && npm audit --audit-level=high
```

Applied upgrade: `next@14.2.35` and `eslint-config-next@14.2.35` (from 14.2.21). This removed the critical Next.js advisory class present on 14.2.21 without jumping to Next 16.

### Runtime advisories (deferred temporarily)

| Package | Severity | Status |
| ------- | -------- | ------ |
| next@14.2.35 | high | **Deferred temporarily.** npm audit affected range still includes all 14.x; patched release requires Next 16.x, a major framework upgrade outside current scope. Requires dedicated upgrade batch with full frontend verification. |

### Dev/tooling advisories

| Package | Severity | Status |
| ------- | -------- | ------ |
| glob@10.3.10 | high | Transitive via eslint-config-next; CLI command injection advisory. **Dev/lint only** during `npm run lint`. Fix path requires eslint-config-next@16.x. Deferred temporarily. |

Moderate advisories (js-yaml via Jest/ts-jest, postcss via next) remain in the full audit report. Address in a dedicated dependency batch with test verification.

Re-check after any `package.json` or lockfile change:

```bash
cd frontend && npm audit --audit-level=high
cd backend && pip-audit
```
