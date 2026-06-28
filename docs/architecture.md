# Architecture

## Overview

ghost-sweep is a multi-surface integrity platform composed of:

- a FastAPI backend
- a PostgreSQL database
- a Redis cache for auth rate limiting and refresh token storage
- a Next.js frontend
- Chrome and Firefox browser extensions

## Core domains

### Users

Registered users submit reports, authenticate with JWT access tokens, and maintain refresh tokens stored in Redis and HttpOnly cookies.

### Companies

Companies are tracked by normalized name. Employers can claim profiles, respond to reports, verify active roles, and dispute incorrect information.

### Job postings

Each posting is keyed by posting URL and linked to a company. Postings track first seen, last seen, and status values such as reported, verified_active, and disputed.

### Reports

Reports require:

- job posting URL
- company name
- job title
- timeline
- evidence
- report category

Reports move through moderation states such as submitted, reviewed, and disputed.

### Scoring

The scoring service calculates transparent ghost job risk signals from report volume, reviewed evidence, posting age, repost patterns, duplicate report categories, and employer verification state.

## Request flow

1. Client authenticates and receives an access token.
2. Client submits a structured report with evidence.
3. Backend validates input, upserts company and posting records, and stores evidence.
4. Clients request posting details and risk score breakdowns.
5. Employers use future moderation and claim workflows to respond and verify postings.

## Security boundaries

- Untrusted input is validated with Pydantic models
- Passwords are hashed with bcrypt
- Access tokens are short-lived JWTs
- Refresh tokens are stored in Redis and delivered in HttpOnly cookies
- Auth endpoints are rate limited
- CORS uses explicit allowlists

## Deployment model

Local development uses Docker Compose. Production deployment is not defined in this repository yet and requires separate approval for environment-specific configuration.

## Non-goals

- Automated legal determinations
- Anonymous unverified accusations without evidence
- Bulk scraping of third-party job boards without policy review
