# Employer API (Batch 6)

Base URL: `http://localhost:8000`

Batch 6 adds employer claim review (Workstream A) and employer responses to integrity reports (Workstream B).

## Employer claims (Workstream A)

See claim routes under `/api/v1/employer-claims`:

- `POST /api/v1/employer-claims` — submit claim (authenticated)
- `GET /api/v1/employer-claims/me` — list caller claims
- `GET /api/v1/employer-claims/{id}` — owner or admin read
- `GET /api/v1/employer-claims` — admin queue (`?status=pending`)
- `POST /api/v1/employer-claims/{id}/approve` — admin approve
- `POST /api/v1/employer-claims/{id}/reject` — admin reject (optional reason in audit metadata)

Claim approval links the user to the company (`is_employer = true`, `employer_company_id` set). It does **not** change `company.verified_status`.

### POST /api/v1/employer-claims

Submit an employer claim for a company. Requires bearer authentication.

Request:

```json
{
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "verification_documents": [
    "https://example.com/domain-verification.pdf"
  ]
}
```

`verification_documents` is **required**: 1 to 10 URL or reference strings (max 2048 characters each). Claims without this field return `422`.

Response `201`:

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "company_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "status": "pending",
  "verification_documents": [
    "https://example.com/domain-verification.pdf"
  ],
  "created_at": "2026-06-29T12:00:00Z",
  "updated_at": "2026-06-29T12:00:00Z"
}
```

Errors:

- `401` when authentication is missing or invalid
- `409` when the user already has a pending or approved claim for the company
- `422` when validation fails (including missing `verification_documents`)

### Admin approve and reject

`POST /api/v1/employer-claims/{claim_id}/approve` requires an admin bearer token. Returns `200` with updated claim status `approved`.

`POST /api/v1/employer-claims/{claim_id}/reject` requires an admin bearer token. Optional JSON body:

```json
{
  "reason": "Domain verification documents were insufficient."
}
```

Reject reasons are stored in audit metadata only.

Admin bootstrap:

```sql
UPDATE users SET is_admin = true WHERE email = 'your@email.com';
```

## POST /api/v1/reports/{report_id}/responses

Submit an employer response to an integrity report. Requires bearer authentication as a verified employer for the report's company (approved claim).

Request:

```json
{
  "response_text": "This role remained open while active interviews were scheduled with candidates.",
  "evidence_urls": ["https://example.com/hiring-proof"]
}
```

Validation:

- `response_text`: 20–5000 characters
- `evidence_urls`: optional list of URL/reference strings (max 10 items, 2048 chars each)

Response `201`: employer response object.

Side effects:

- When report status is `pending` or `verified`, status moves to `disputed`
- Recalculates job posting and company scores
- Inserts score snapshots
- Writes audit log entry (`employer_response.created`)

Multiple responses per report are allowed in Batch 6.

Errors:

- `401` when authentication is missing or invalid
- `403` when the caller is not a verified employer for the report's company
- `404` when the report does not exist
- `422` when validation fails

## GET /api/v1/reports/{report_id}/responses

Return employer responses linked to a report. Public read; no authentication required.

Response `200`:

```json
{
  "items": [],
  "total": 0
}
```

Errors:

- `404` when the report does not exist

## Related documentation

- [moderation-api.md](moderation-api.md) — admin verify/dismiss flows
- [domain-api.md](domain-api.md) — report and vote APIs
- [moderation-model.md](moderation-model.md) — product moderation principles
