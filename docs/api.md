# API Reference

Base URL: `http://localhost:8000`

This document lists endpoints implemented in the current codebase. Domain APIs for companies, reports, and job postings are planned for future batches and are not available yet.

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

Batch 3 implements access-token-only authentication. See [auth-api.md](auth-api.md) for request and response details.

Implemented endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

Deferred to Batch 4:

- Refresh tokens
- Logout
- HttpOnly cookies
- Redis-backed session or token storage
- Auth rate limiting

## Future batches

The following API areas are not implemented yet:

- Company APIs (planned for a future batch)
- Report APIs (planned for a future batch)
- Job posting APIs (planned for a future batch)

Do not treat these endpoints as available until their batch is shipped and documented here.

## Error model

Common HTTP status codes in the current API:

- `401` authentication failure
- `404` resource not found
- `409` conflict such as duplicate account
- `422` validation or business rule failure

Stack traces are not exposed to clients.
