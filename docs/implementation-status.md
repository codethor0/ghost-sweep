# Implementation Status

Summary of implemented scope through Batch 6B. For API details see [api.md](api.md).

## Authentication

Refresh tokens are opaque strings stored in Redis by SHA-256 hash. The refresh endpoint returns a new access token but **does not rotate** the refresh token; the same refresh token string is returned until expiry or logout revokes it.

## Backend (Batch 6B complete)

- Auth: register, login, me, refresh, logout, rate limiting
- Company and job posting read APIs with score breakdowns
- Reports, votes, employer claims, moderation, employer responses
- Scoring recalculation, score snapshots, audit logging

## Scaffold

- Frontend: health probe, extension posting URL display; no auth or report UI
- Extension: MV3 popup with posting URL handoff to frontend query parameter

## Deferred

See README current project status and [dependency-audit.md](dependency-audit.md).
