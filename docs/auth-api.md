# Authentication API

Base URL: `http://localhost:8000`

Authentication uses short-lived JWT access tokens plus opaque refresh tokens delivered in JSON response bodies. Protected routes accept `Authorization: Bearer <access_token>`.

Refresh tokens are stored in Redis by SHA-256 hash only. Logout revokes the refresh token only; access tokens remain valid until their JWT expiration time.

Deferred to future batches:

- HttpOnly cookies (refresh tokens are JSON-body delivered today)
- Redis health reporting in `/health`
- Evidence upload
- Moderation status transition APIs

## POST /api/v1/auth/register

Register a user and receive access and refresh tokens.

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
  "refresh_token": "opaque-token",
  "token_type": "bearer"
}
```

Errors:

- `409` when the email is already registered
- `409` when the username is already taken
- `422` when request validation fails
- `429` when the auth rate limit is exceeded

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
  "refresh_token": "opaque-token",
  "token_type": "bearer"
}
```

Invalid credentials always return `401`:

```json
{
  "detail": "Invalid credentials"
}
```

Rate limiting returns `429`:

```json
{
  "detail": "Too many requests"
}
```

## POST /api/v1/auth/refresh

Exchange a valid refresh token for a new access token. Batch 4 does not rotate refresh tokens; the same refresh token is returned.

Request:

```json
{
  "refresh_token": "opaque-token"
}
```

Response `200`:

```json
{
  "access_token": "jwt",
  "refresh_token": "opaque-token",
  "token_type": "bearer"
}
```

Errors:

- `401` when the refresh token is missing, expired, or revoked
- `429` when the auth rate limit is exceeded

## POST /api/v1/auth/logout

Revoke a refresh token. Existing access tokens remain valid until expiration.

Request:

```json
{
  "refresh_token": "opaque-token"
}
```

Response `204 No Content`

Logout is not rate-limited.

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

## Refresh token format

Refresh tokens are opaque random strings generated server-side. Only the SHA-256 hash is stored in Redis under `refresh:{token_hash}` with TTL `REFRESH_TOKEN_EXPIRE_DAYS * 86400` (default 14 days).

## Auth rate limiting

Register, login, and refresh are rate-limited per client IP and route using Redis keys `auth_rl:{route}:{ip}` with a 60-second window. The limit follows `AUTH_RATE_LIMIT_PER_MINUTE` (default 20).

Logout is excluded from rate limiting.
