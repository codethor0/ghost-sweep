# Dependency Audit Status

This document records known dependency advisories that remain after the smallest safe upgrades applied during pre-6C remediation. Do not hide new failures; re-run audits after dependency changes.

## Backend: pip-audit

Command:

```bash
cd backend && pip-audit
```

Status at pre-6C remediation: **16 known vulnerabilities in 6 packages** (dev and transitive tooling).

| Package | Notes |
| ------- | ----- |
| black | Dev dependency |
| loguru | Transitive |
| pip | Tooling |
| pytest | Dev dependency |
| starlette | Transitive via FastAPI |
| wheel | Tooling |

CI runs pip-audit with `continue-on-error: true` so advisories remain visible without blocking the gate until remediated or formally accepted.

## Frontend: npm audit

Command:

```bash
cd frontend && npm audit --audit-level=high
```

Applied upgrade: `next@14.2.35` and `eslint-config-next@14.2.35` (from 14.2.21). This removed the critical Next.js advisory class present on 14.2.21 without jumping to Next 16.

Remaining high advisories after 14.2.35:

| Package | Severity | Reason deferred |
| ------- | -------- | --------------- |
| next@14.2.35 | high | npm audit affected range still includes all 14.x; patched release requires Next 16.x (`next@16.2.9`), which is a major framework upgrade outside pre-6C remediation scope |
| glob@10.3.10 | high | Transitive via `eslint-config-next@14.2.35` / `@next/eslint-plugin-next`; GHSA-5j98-mcp5-4vw2 (CLI command injection). Fix path requires `eslint-config-next@16.x` |

Moderate advisories (js-yaml via Jest/ts-jest, postcss via next) remain in the full audit report. Address in a dedicated dependency batch with test verification.

Re-check after any `package.json` or lockfile change:

```bash
cd frontend && npm audit --audit-level=high
```
