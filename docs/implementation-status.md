# Implementation Status

Summary of implemented scope through Batch 6C. For API details see [api.md](api.md).

## Authentication

Refresh tokens are opaque strings stored in Redis by SHA-256 hash. The refresh endpoint returns a new access token but **does not rotate** the refresh token; the same refresh token string is returned until expiry or logout revokes it.

## Backend (Batch 6B complete)

- Auth: register, login, me, refresh, logout, rate limiting
- Company and job posting read APIs with score breakdowns
- Reports, votes, employer claims, moderation, employer responses
- Scoring recalculation, score snapshots, audit logging

## Frontend (Batch 6C complete)

- API client for health, auth, companies, job postings, reports, and score endpoints
- Pages: register, login, dashboard, companies list, company detail, posting detail, report form
- Access tokens stored in React state only; cleared on refresh or sign out
- Refresh token handling is not wired in the frontend
- Session is intentionally lost on page refresh
- Home page health probe and extension `posting_url` handoff display

## Extension (scaffold)

- MV3 popup for Chrome and Firefox
- Reads active tab URL and opens frontend with `?posting_url=`
- No backend API calls; Batch 6D not started

## Local demo seed

- `backend/scripts/seed_demo_data.py` creates one demo company and job posting in development only (idempotent)

## Public MVP (static site)

- Standalone static site in `public-mvp/` for GitHub Pages (HTML/CSS only; no build step)
- Report intake via Google Form placeholder URL; manual review via Google Sheet
- GitHub Pages hosts static content only; no FastAPI, PostgreSQL, or Redis
- Full Next.js frontend remains server-mode for local Docker; not deployed to Pages
- Live public scoring database not hosted yet
- Google Form URL is placeholder until form is created
- Validation: `python3.11 scripts/validate_public_mvp.py`

See [free-public-launch-plan.md](free-public-launch-plan.md) and [google-form-intake-spec.md](google-form-intake-spec.md).

## Deferred

- Evidence file upload
- Public company and job posting write APIs
- Extension API integration (Batch 6D)
- Frontend moderation, employer, and admin UI
- Frontend refresh-token persistence
- Release hardening
- Public backend hosting
- Google Sheet to PostgreSQL import automation

See README current project status and [dependency-audit.md](dependency-audit.md).
