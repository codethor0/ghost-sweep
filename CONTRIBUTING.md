# Contributing to ghost-sweep

Thank you for helping improve hiring transparency.

## Before you start

1. Read `README.md`, `AGENTS.md`, and `docs/architecture.md`
2. Search existing issues and pull requests
3. Open an issue for substantial changes before starting work

## Development setup

See `README.md` for local setup and verification commands.

## Public MVP vs full-stack development

ghost-sweep has two paths:

| Path | Location | Purpose |
| ---- | -------- | ------- |
| Public MVP | `public-mvp/` | Static GitHub Pages site; report intake via Google Form |
| Full application | `backend/`, `frontend/`, Docker Compose | Local API, database, and Next.js UI |

Contributors working on the API, scoring, auth, or Next.js pages should use the Docker stack. The public MVP is plain HTML/CSS with no build step. Do not convert the full Next.js app to static export without approval.

Public MVP validation:

```bash
python3.11 scripts/validate_public_mvp.py
python3 -m http.server 8080 --directory public-mvp
```

Extension API integration (Batch 6D) remains deferred. Evidence file upload and public backend hosting are deferred.

## Pull request requirements

Every pull request must include:

- What changed
- Why it changed
- How it was tested
- Security impact
- Data and privacy impact
- Screenshots for UI changes
- Rollback plan

## Code standards

- No placeholders, stubs, or TODO comments
- No emojis in code, comments, commits, documentation, or test names
- Backend functions require type hints; public functions require Google-style docstrings
- Frontend components require explicit Props interfaces and strict TypeScript
- All list endpoints must paginate
- All scoring changes must include tests and documentation updates

## Testing expectations

- Backend coverage target: 80 percent
- Frontend coverage target: 70 percent
- Do not skip tests unless an issue link and explanation are provided

## Dependency changes

Open an issue or pull request note that includes:

- Exact package name and version
- Why it is needed
- Security or maintenance risk
- Alternative options

## Signed commits

Signed commits are preferred.

## Community

All contributors must follow `CODE_OF_CONDUCT.md`.
