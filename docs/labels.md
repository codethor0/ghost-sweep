# GitHub Label Taxonomy

Recommended labels for ghost-sweep issues and pull requests. Maintainers create these in the GitHub UI or via API when ready.

This document does not create labels automatically. See [Creating labels](#creating-labels) for optional commands.

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
| `batch-6e` | Contributor readiness batch (templates, labels docs, PR guardrails) |

## Usage guidance

- Apply one **area** label and one **type** label when possible.
- Use `help wanted` or `good first issue` for contributor lanes with clear acceptance criteria.
- Use `blocked:*` instead of closing when work depends on maintainer input.
- Do not use labels to bypass review requirements in `CONTRIBUTING.md` or `AGENTS.md`.

## Creating labels

Run only when explicitly approved. Example commands for maintainers:

```bash
gh label create "good first issue" --color "7057ff" --description "Good for newcomers"
gh label create "help wanted" --color "008672" --description "Extra attention is needed"
gh label create "area:backend" --color "1d76db" --description "Backend Python/FastAPI"
gh label create "area:frontend" --color "1d76db" --description "Next.js frontend"
gh label create "area:docs" --color "1d76db" --description "Documentation"
gh label create "area:public-mvp" --color "1d76db" --description "Static public MVP site"
gh label create "area:extension" --color "1d76db" --description "Browser extension"
gh label create "area:tests" --color "1d76db" --description "Tests and verification"
gh label create "type:bug" --color "d73a4a" --description "Something is not working"
gh label create "type:docs" --color "0075ca" --description "Documentation improvement"
gh label create "type:feature" --color "a2eeef" --description "New feature or request"
gh label create "type:validation" --color "fbca04" --description "Verification or audit work"
gh label create "blocked:needs-design" --color "b60205" --description "Needs maintainer design decision"
gh label create "blocked:external" --color "b60205" --description "Blocked on external dependency"
gh label create "batch-6e" --color "5319e7" --description "Batch 6E contributor readiness"
```

Existing labels such as `bug` and `enhancement` may remain from earlier templates. Prefer the `type:*` labels for new issues when the taxonomy above is active.

## Related documents

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [contributor-onboarding.md](contributor-onboarding.md)
- [implementation-status.md](implementation-status.md)
