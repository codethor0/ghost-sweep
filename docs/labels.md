# GitHub Label Taxonomy

Recommended labels for ghost-sweep issues and pull requests. The taxonomy below reflects the live label set on GitHub (22 labels total).

## Default and legacy labels (preserved)

GitHub default labels remain for backward compatibility. Do not delete them.

| Label | Purpose |
| ----- | ------- |
| `bug` | Legacy default defect label |
| `documentation` | Legacy default documentation label |
| `duplicate` | Duplicate issue or pull request |
| `enhancement` | Legacy default feature request label |
| `invalid` | Invalid or off-topic report |
| `question` | Further information requested |
| `wontfix` | Will not be worked on |

Prefer the `type:*` labels for new issues when the taxonomy below is active.

## Contributor discovery

| Label | Purpose |
| ----- | ------- |
| `good first issue` | Small, well-scoped task suitable for a first contribution |
| `help wanted` | Maintainer welcomes external help; scope is documented |

## Area

| Label | Purpose |
| ----- | ------- |
| `area:backend` | FastAPI services, models, tests under `backend/` |
| `area:frontend` | Next.js app under `frontend/` |
| `area:docs` | Documentation under `docs/` or root markdown |
| `area:public-mvp` | Static site under `public-mvp/` |
| `area:extension` | Browser extension under `extension/` |
| `area:tests` | Test-only or verification-focused work |

## Type

| Label | Purpose |
| ----- | ------- |
| `type:bug` | Reproducible defect |
| `type:docs` | Documentation correction or gap fill |
| `type:feature` | New capability (requires design approval when it touches API or schema) |
| `type:validation` | Verification, audit, or launch-readiness work |

## Blocked

| Label | Purpose |
| ----- | ------- |
| `blocked:needs-design` | Waiting on maintainer design or policy decision |
| `blocked:external` | Blocked on external input (Form URL, billing, hosting, etc.) |

## Batch tracking

| Label | Purpose |
| ----- | ------- |
| `batch-6e` | Contributor readiness batch (templates, labels, PR guardrails) |

## Recommended labels for Issue #1

Issue #1 (Contributor onboarding: job URL validation pipeline) uses:

- `help wanted`
- `good first issue`
- `area:backend`
- `batch-6e`

## Usage guidance

- Apply one **area** label and one **type** label when possible.
- Use `help wanted` or `good first issue` for contributor lanes with clear acceptance criteria.
- Use `blocked:*` instead of closing when work depends on maintainer input.
- Do not use labels to bypass review requirements in `CONTRIBUTING.md` or `AGENTS.md`.
- Do not delete legacy labels; prefer `type:*` for new issues.

## Label inventory (22 total)

| Category | Count | Labels |
| -------- | ----- | ------ |
| Legacy/default | 7 | bug, documentation, duplicate, enhancement, invalid, question, wontfix |
| Contributor discovery | 2 | good first issue, help wanted |
| Area | 6 | area:backend, area:frontend, area:docs, area:public-mvp, area:extension, area:tests |
| Type | 4 | type:bug, type:docs, type:feature, type:validation |
| Blocked | 2 | blocked:needs-design, blocked:external |
| Batch | 1 | batch-6e |

## Related documents

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [contributor-onboarding.md](contributor-onboarding.md)
- [implementation-status.md](implementation-status.md)
