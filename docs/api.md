# API Reference

Base URL: `http://localhost:8000`

## Health

### GET /health

Returns database and Redis health.

Response:

```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy"
}
```

## Authentication

### POST /api/v1/auth/register

Register a user and receive an access token. Refresh token is set in an HttpOnly cookie.

Request:

```json
{
  "email": "user@example.com",
  "username": "seeker1",
  "password": "StrongPass123!"
}
```

Response:

```json
{
  "access_token": "jwt",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/login

Authenticate with email or username.

Request:

```json
{
  "identifier": "user@example.com",
  "password": "StrongPass123!"
}
```

Invalid credentials always return:

```json
{
  "detail": "Invalid credentials"
}
```

### POST /api/v1/auth/refresh

Exchange a refresh token for a new access token using either request body or HttpOnly cookie.

## Companies

### GET /api/v1/companies?page=1&page_size=20

Returns paginated company records.

### POST /api/v1/companies

Create a company profile. Requires bearer authentication.

## Reports

### POST /api/v1/reports

Submit an evidence-based report. Requires bearer authentication.

Request:

```json
{
  "company_name": "Example Corp",
  "job_title": "Backend Engineer",
  "posting_url": "https://example.com/jobs/backend-engineer",
  "category": "stale_repost",
  "timeline_description": "Posting remained open for several months without updates.",
  "evidence": [
    {
      "evidence_type": "screenshot",
      "source_url": "https://example.com/evidence/1",
      "description": "Screenshot showing repeated repost activity."
    }
  ]
}
```

Validation failures return HTTP 422 when evidence is missing or business rules fail.

## Job postings

### GET /api/v1/job-postings/{id}

Return posting metadata.

### GET /api/v1/job-postings/{id}/risk-score

Return transparent risk signal breakdown:

```json
{
  "job_posting_id": 1,
  "score": 0.7425,
  "confidence": 0.75,
  "explanation": "Risk signal based on reported user activity...",
  "components": [
    {
      "name": "report_volume",
      "raw_value": 0.8,
      "weight": 0.3,
      "weighted_value": 0.24
    }
  ],
  "calculated_at": "2026-06-28T00:00:00Z"
}
```

## Error model

- `401` authentication failure
- `404` resource not found
- `409` conflict such as duplicate account
- `422` validation or business rule failure

Stack traces are not exposed to clients.
