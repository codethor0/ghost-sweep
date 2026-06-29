# Moderation API (Batch 6B)

Base URL: `http://localhost:8000`

Admin-only endpoints for report moderation. Requires a bearer access token for a user with `is_admin = true`.

Admin bootstrap (local development):

```sql
UPDATE users SET is_admin = true WHERE email = 'your@email.com';
```

## GET /api/v1/moderation/reports

Return a paginated moderation queue filtered by report status.

Query parameters:

- `status` (default `pending`): `pending`, `verified`, `dismissed`, or `disputed`
- `page` (default 1)
- `page_size` (default 20, max 100)

Response `200`: paginated list of `ReportResponse` objects.

Errors:

- `401` when authentication is missing or invalid
- `403` when the caller is not an admin

## POST /api/v1/moderation/reports/{report_id}/verify

Mark a report as verified after admin review.

Allowed transitions:

- `pending` → `verified`
- `disputed` → `verified`

Response `200`: updated report object.

Side effects:

- Recalculates job posting and company scores
- Inserts score snapshots
- Writes audit log entry (`report.verified`)

Errors:

- `401` / `403` as above
- `404` when the report does not exist
- `422` when the report status cannot transition to verified

## POST /api/v1/moderation/reports/{report_id}/dismiss

Dismiss a report after admin review.

Allowed transitions:

- `pending` → `dismissed`
- `disputed` → `dismissed`

Optional request body:

```json
{
  "reason": "Optional dismissal reason stored in audit metadata only."
}
```

Response `200`: updated report object.

Side effects:

- Recalculates job posting and company scores
- Inserts score snapshots
- Writes audit log entry (`report.dismissed`) with optional `reason` in metadata

Errors:

- `401` / `403` as above
- `404` when the report does not exist
- `422` when the report status cannot transition to dismissed

Dismissed reports are terminal in Batch 6. They cannot be reopened through the API.

## State machine summary

| From | Action | To |
| ---- | ------ | -- |
| `pending` | verify | `verified` |
| `pending` | dismiss | `dismissed` |
| `pending` | employer response | `disputed` |
| `verified` | employer response | `disputed` |
| `disputed` | verify | `verified` |
| `disputed` | dismiss | `dismissed` |

Employer responses are documented in [employer-api.md](employer-api.md).
