# Authentication API (Batch 3)

Base URL: `http://localhost:8000`

Batch 3 provides access-token-only authentication. Register and login return a bearer JWT access token in the JSON response body. Protected routes accept `Authorization: Bearer <access_token>`.

Deferred to Batch 4:

- Refresh tokens
- Logout
- HttpOnly cookies
- Redis-backed session or token storage
- Auth rate limiting

## POST /api/v1/auth/register

Register a user and receive an access token.

Request:

```json
{
  "email": "user@example.com",
  "username": "seeker1",
  "password": "StrongPass123!"
}
```

Validation:

- `email`: valid email address
- `username`: 3-64 characters, alphanumeric plus `_` and `-`
- `password`: 12-128 characters

Response `200`:

```json
{
  "access_token": "jwt",
  "token_type": "bearer"
}
```

Errors:

- `409` when the email is already registered
- `409` when the username is already taken
- `422` when request validation fails

## POST /api/v1/auth/login

Authenticate with email or username.

Request:

```json
{
  "identifier": "user@example.com",
  "password": "StrongPass123!"
}
```

Response `200`:

```json
{
  "access_token": "jwt",
  "token_type": "bearer"
}
```

Invalid credentials always return `401`:

```json
{
  "detail": "Invalid credentials"
}
```

## GET /api/v1/auth/me

Return the authenticated user's profile. Requires a valid bearer access token.

Response `200`:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "seeker1",
  "reputation_score": 0.0,
  "report_weight": 1.0,
  "is_employer": false,
  "is_admin": false,
  "employer_company_id": null,
  "created_at": "2026-01-01T00:00:00Z"
}
```

Errors:

- `401` when the bearer token is missing, invalid, or expired

## Access token format

Access tokens are signed JWTs with:

- `sub`: user UUID
- `exp`: expiration timestamp
- `type`: `"access"`

Token lifetime follows `ACCESS_TOKEN_EXPIRE_MINUTES` (default 15 minutes).

Invalid, expired, missing, or wrong-type tokens are rejected with `401 Unauthorized`.
