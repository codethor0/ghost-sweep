# ghost-sweep Development Doctrine

## Mission

ghost-sweep is an open-source, community-driven Job Integrity Database designed to expose ghost jobs, restore transparency to hiring, and help job seekers decide which companies and job postings are worth their time.

This is an integrity application. The code must reflect that.

## Non-Negotiable Standard

This project follows a zero-known-bug release standard.

No feature is complete until it is implemented, tested, documented, reviewed, and verified.

No placeholders.
No fake functionality.
No hallucinated APIs.
No emojis in code, comments, commits, documentation, test names, or generated files.

## Operating Rules

Before making changes, read the relevant files completely.

Never modify code based on partial context.

Never invent APIs, package names, framework behavior, database fields, or test commands.

If uncertain, stop and state the uncertainty.

If a dependency is needed, request approval first and provide:

- Exact package name
- Exact version
- Why it is needed
- Security or maintenance risk
- Alternative options

## Locked Stack

Backend:

- Python 3.11
- FastAPI
- SQLAlchemy 2.0 async
- Alembic
- Pydantic v2
- PostgreSQL 15
- Redis 7

Frontend:

- Next.js 14
- React
- TypeScript strict mode
- Tailwind CSS

Extension:

- Chrome and Firefox Manifest V3

Security:

- bcrypt for password hashing
- JWT access tokens
- Refresh tokens stored securely
- Server-side validation
- No raw SQL except migrations
- No hardcoded secrets

Testing:

- pytest
- httpx
- mypy strict
- black
- flake8
- ESLint
- Prettier
- Jest
- React Testing Library
- Bandit
- pip-audit
- npm audit

## Allowed Without Approval

Contributors may:

- Edit application code
- Add tests
- Fix failing tests
- Improve documentation
- Refactor without changing behavior
- Run linting, type checks, tests, and audits
- Add docstrings and comments
- Improve error messages

## Requires Approval

Contributors must ask before:

- Adding dependencies
- Changing database schema
- Creating migrations
- Changing auth logic
- Changing scoring formulas
- Modifying CI/CD
- Modifying Docker configuration
- Changing API response contracts
- Deleting files
- Changing project architecture
- Touching secrets, environment variables, or deployment config

## Forbidden

Contributors must never:

- Add TODO comments
- Add placeholder code
- Add stubs
- Use pass, ellipsis, or NotImplementedError as final code
- Hardcode secrets
- Use raw SQL in app code
- Swallow exceptions silently
- Use broad exception handling without logging and re-raising
- Skip tests
- Remove tests to make builds pass
- Use TypeScript any without justification
- Add emojis anywhere
- Claim success without running verification
- Mark work complete when checks fail

## Release Rule

Do not release until all verification gates in `README.md` pass and required documentation is complete.

See `docs/architecture.md`, `docs/api.md`, `docs/scoring-algorithm.md`, `docs/moderation-model.md`, and `docs/legal-risk.md` for product and implementation guidance.
