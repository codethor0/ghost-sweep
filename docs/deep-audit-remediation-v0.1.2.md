# Deep Audit Remediation (planned v0.1.2)

This document summarizes remediation work prepared after the independent deep audit of 2026-07-10. The changes are implemented on branch `fix/deep-audit-remediation-v0.1.2` and are not released until review, merge, and a separate release batch publish `v0.1.2`.

## High-severity fixes

- Public report list, detail, and employer-response reads return only `verified` reports.
- Public schemas omit reporter and employer-user UUIDs.
- Score calculation uses only verified reports.
- Pending report creation no longer changes public scores.
- Duplicate active report submissions are rejected with `409 Conflict`.
- Report submission rate limiting is enforced separately from auth rate limits.
- Employer response scoring counts distinct eligible reports with responses.
- Duplicate employer responses from the same account are rejected.

## Secondary fixes

- Community votes update `verification_votes` from persisted vote records.
- Refresh tokens rotate on use; reused tokens are rejected.
- Frontend logout calls backend revocation and clears in-memory session tokens.
- Next.js App Router pages await asynchronous `searchParams`.
- Sheet import dry runs require `reviewer` and `reviewed_at`, expand PII scanning, and avoid shared ATS hosts as company domains.
- Supported ATS providers map to `company_site` instead of `other`.
- Email and username uniqueness is case-insensitive.
- Passwords above bcrypt's UTF-8 byte boundary are rejected.
- `/health` remains liveness-only; `/health/ready` checks PostgreSQL and Redis.
- Audit bundle packaging excludes macOS `._*` metadata and sets `COPYFILE_DISABLE=1`.

## Migration

`003_audit_remediation` adds:

- case-insensitive unique indexes on `users.email` and `users.username`
- unique index on `employer_responses (report_id, user_id)`
- partial unique index blocking duplicate active reports per reporter/posting/type

The migration fails if unresolved case-equivalent user collisions already exist.

## Dependency PR interaction

Dependency file changes remain in open PRs #21, #22, #32, and #35. This remediation branch does not duplicate those updates.

## Release status

- `v0.1.0` unchanged
- `v0.1.1` unchanged
- `v0.1.2` not created in this batch
