# Architecture

## Overview

ghost-sweep is a multi-surface integrity platform composed of:

- a FastAPI backend
- a PostgreSQL database
- a Redis cache for auth rate limiting and refresh token storage
- a Next.js frontend (scaffold)
- Chrome and Firefox browser extensions (scaffold)

## Core domains

### Users

Registered users authenticate with short-lived JWT access tokens. Refresh tokens are opaque strings returned in JSON response bodies and stored in Redis by SHA-256 hash only. HttpOnly cookie transport is deferred to a future batch.

### Companies

Companies are tracked by normalized name. Employer claim, response, and verification workflows are planned but not implemented in the current API.

### Job postings

Each posting is keyed by posting URL and linked to a company. Postings track detection time, last seen time, and lifecycle status values such as `active`, `filled`, `removed`, `suspected_ghost`, and `disputed`.

### Reports

Current report creation requires:

- an existing job posting identifier
- a report category (`report_type`)
- a text description (minimum 20 characters)

Evidence file upload is deferred. Reports are created with status `pending`. Moderation transitions to `verified`, `dismissed`, or `disputed` are not implemented yet.

### Scoring

The scoring service calculates transparent ghost job risk signals from posting age, repost patterns, company integrity history, verified report counts, and related inputs documented in [scoring-algorithm.md](scoring-algorithm.md).

## Request flow (implemented)

1. Client registers or logs in and receives access and refresh tokens in JSON.
2. Client submits a structured report for an existing job posting (authentication required).
3. Backend stores the report, increments company report count, recalculates scores, and writes audit logs.
4. Clients request company, posting, and score breakdown details via public read endpoints.
5. Authenticated users may vote on reports; duplicate votes return `409`.

Employer claim, evidence upload, and moderation review flows are future work.

## Security boundaries (implemented)

- Untrusted input is validated with Pydantic models
- Passwords are hashed with bcrypt
- Access tokens are short-lived JWTs delivered as bearer tokens
- Refresh tokens are stored in Redis by hash and delivered in JSON response bodies
- Auth endpoints are rate limited per client IP and route using atomic Redis operations
- CORS uses explicit allowlists
- `/health` returns basic service metadata only; it does not verify PostgreSQL or Redis connectivity

## Deployment model

Local development uses Docker Compose. Production deployment is not defined in this repository yet and requires separate approval for environment-specific configuration.

Production and staging require an explicit `JWT_SECRET_KEY` of at least 32 characters. Development may use a local-only default when unset.

## Non-goals

- Automated legal determinations
- Claiming unimplemented moderation or evidence guarantees in API behavior
- Bulk scraping of third-party job boards without policy review
