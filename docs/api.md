# API Reference

Base URL: `http://localhost:8000`

This document lists endpoints implemented in the current codebase.

## Service metadata

### GET /

Return API metadata.

Response:

```json
{
  "service": "ghost-sweep",
  "status": "ok",
  "api_prefix": "/api/v1"
}
```

## Health

### GET /health

Return basic service health. Database and Redis checks are not included in the current implementation.

Response:

```json
{
  "status": "ok",
  "service": "ghost-sweep"
}
```

## Authentication

See [auth-api.md](auth-api.md) for request and response details.

Implemented endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Register, login, and refresh are rate-limited per client IP and route. Logout returns `204 No Content` and revokes the refresh token only; access tokens remain valid until expiration.

## Domain APIs

See [domain-api.md](domain-api.md) for report and vote endpoints.

## Employer and moderation APIs

See [employer-api.md](employer-api.md) and [moderation-api.md](moderation-api.md).

Implemented endpoints:

- `GET /api/v1/companies`
- `GET /api/v1/companies/{company_id}`
- `GET /api/v1/companies/{company_id}/integrity-score`
- `GET /api/v1/job-postings/{job_posting_id}`
- `GET /api/v1/job-postings/{job_posting_id}/risk-score`
- `POST /api/v1/reports`
- `GET /api/v1/reports/{report_id}`
- `GET /api/v1/reports?job_posting_id={uuid}`
- `POST /api/v1/reports/{report_id}/votes`
- `GET /api/v1/reports/{report_id}/responses`
- `POST /api/v1/reports/{report_id}/responses`
- `POST /api/v1/employer-claims`
- `GET /api/v1/employer-claims/me`
- `GET /api/v1/employer-claims/{claim_id}`
- `GET /api/v1/employer-claims`
- `POST /api/v1/employer-claims/{claim_id}/approve`
- `POST /api/v1/employer-claims/{claim_id}/reject`
- `GET /api/v1/moderation/reports`
- `POST /api/v1/moderation/reports/{report_id}/verify`
- `POST /api/v1/moderation/reports/{report_id}/dismiss`

Deferred to future batches:

- HttpOnly cookies (refresh tokens are JSON-body delivered today)
- Redis health reporting in `/health`
- Evidence file upload
- Company and job posting write APIs (public)
- Extension API integration (Batch 6D)
- Frontend moderation, employer, and admin UI
- URL-to-posting lookup from extension handoff

## Error model

Common HTTP status codes in the current API:

- `401` authentication failure
- `403` forbidden (admin or employer permission required)
- `404` resource not found
- `409` conflict such as duplicate account or duplicate vote
- `422` validation or business rule failure
- `429` auth rate limit exceeded

Stack traces are not exposed to clients.
