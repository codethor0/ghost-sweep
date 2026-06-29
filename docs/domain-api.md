# Domain API (Batch 5)

Base URL: `http://localhost:8000`

Batch 5 adds read-only company and job posting endpoints plus authenticated report and vote writes. Scores are recalculated and snapshotted when reports and votes are created.

Public reads do not require authentication. Report and vote creation require a bearer access token. See [auth-api.md](auth-api.md).

Deferred to later batches:

- Evidence upload
- Company and job posting create/update/delete (public write APIs)
- Extension API integration (Batch 6D)
- URL-to-posting lookup from extension handoff

## GET /api/v1/companies

Return a paginated list of companies.

Query parameters:

- `page` (default 1)
- `page_size` (default 20, max 100)

Response `200`:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

## GET /api/v1/companies/{company_id}

Return a company profile.

Response `200`: company object matching `CompanyResponse`.

Errors:

- `404` when the company does not exist

## GET /api/v1/companies/{company_id}/integrity-score

Return the current integrity score breakdown for a company.

Response `200`:

```json
{
  "score": 72.5,
  "breakdown": {
    "post_to_hire_ratio": 10.0,
    "report_ratio": 18.0
  }
}
```

Errors:

- `404` when the company does not exist

## GET /api/v1/job-postings/{job_posting_id}

Return a job posting profile.

Response `200`: posting object matching `JobPostingResponse`.

Errors:

- `404` when the job posting does not exist

## GET /api/v1/job-postings/{job_posting_id}/risk-score

Return the current ghost job risk score breakdown for a posting.

Response `200`:

```json
{
  "score": 64.0,
  "breakdown": {
    "posting_age": 12.5,
    "repost_history": 8.0
  }
}
```

Errors:

- `404` when the job posting does not exist

## POST /api/v1/reports

Submit an integrity report for a job posting. Requires bearer authentication.

Request:

```json
{
  "job_posting_id": "uuid",
  "report_type": "stale_posting",
  "description": "The posting remained active without recruiter follow-up for several months."
}
```

`report_type` values: `ghost_job`, `no_response`, `scam`, `data_harvest`, `repost_loop`, `stale_posting`, `fake_interview`

Response `201`: report object matching `ReportResponse` with `status: "pending"`.

Report status values in the schema: `pending`, `verified`, `dismissed`, `disputed`. New reports start as `pending`.

Moderation transitions are implemented in Batch 6:

- Admins verify or dismiss reports via `/api/v1/moderation/reports/{id}/verify|dismiss`
- Verified employers dispute reports by submitting `/api/v1/reports/{id}/responses` (moves `pending` or `verified` → `disputed`)

See [moderation-api.md](moderation-api.md) and [employer-api.md](employer-api.md).

Side effects:

- Increments company `report_count`
- Recalculates job posting and company scores
- Inserts score snapshots
- Writes an audit log entry (`report.created`)

Errors:

- `401` when authentication is missing or invalid
- `404` when the job posting does not exist
- `422` when validation fails

## GET /api/v1/reports/{report_id}

Return a submitted report.

Response `200`: report object matching `ReportResponse`.

Errors:

- `404` when the report does not exist

## GET /api/v1/reports?job_posting_id={uuid}

List reports linked to a job posting.

Query parameters:

- `job_posting_id` (required UUID)
- `page` (default 1)
- `page_size` (default 20, max 100)

Response `200`:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

Errors:

- `404` when the job posting does not exist

## POST /api/v1/reports/{report_id}/votes

Cast a community vote on a report. Requires bearer authentication.

Request:

```json
{
  "vote": "up"
}
```

`vote` values: `up`, `down`

Response `201`: vote object matching `VoteResponse`.

Side effects:

- Recalculates job posting and company scores
- Inserts score snapshots
- Writes an audit log entry (`vote.created`)

Errors:

- `401` when authentication is missing or invalid
- `404` when the report does not exist
- `409` when the user already voted on the report (including concurrent duplicate requests)
- `422` when validation fails

## Scoring notes

Score formulas remain defined in [scoring-algorithm.md](scoring-algorithm.md). Batch 5 recalculates scores after report and vote writes and stores historical values in `score_snapshots`.

Language risk signals default to `0.0` until a future analysis batch adds supported inputs.

## Audit notes

Batch 5 writes audit logs for report and vote creation. Batch 6 adds audit logs for employer claim review, report moderation transitions, and employer responses. Read endpoints are not audited.
