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

See [auth-api.md](auth-api.md) for request and response details.

Implemented endpoints:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

Register, login, and refresh are rate-limited per client IP and route. Logout returns `204 No Content` and revokes the refresh token only; access tokens remain valid until expiration.

Deferred to future batches:

- HttpOnly cookies
- Redis health reporting in `/health`

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
- `429` auth rate limit exceeded

Stack traces are not exposed to clients.
