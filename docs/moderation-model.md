# Moderation Model

ghost-sweep is evidence-based and community moderated. It is not a defamation platform.

## Report requirements (current API)

Report creation currently requires:

- `job_posting_id` referencing an existing posting
- `report_type` category
- `description` text (minimum 20 characters)

Evidence file upload is **deferred**. The `evidence_files` table exists in the schema, but there is no upload endpoint in the current API. Reports are accepted without attached files today.

Future batches may require evidence attachments before promotion or verification.

## Report states (schema)

| State | Meaning |
| ----- | ------- |
| `pending` | Received; default on create |
| `verified` | Moderator or trusted process confirmed the report |
| `dismissed` | Report rejected or insufficient |
| `disputed` | Employer or reviewer challenged the report |

Moderation APIs that transition between these states are **not implemented** in the current batch. New reports always start as `pending`.

## Abuse prevention

The platform must prevent:

- brigading
- false reports
- competitor manipulation
- duplicate reporting abuse
- spam
- scraping abuse
- PII exposure
- retaliation risk

Current technical controls include:

- authenticated report and vote submissions
- duplicate vote protection per user and report (`409` on conflict, including race-safe handling)
- auth endpoint rate limiting
- transparent scoring instead of accusatory labels

Future controls may include reputation thresholds, moderator queues, evidence validation, and employer verification workflows.

## Employer rights

Employers must be able to:

- claim a company profile
- respond to reports
- verify active roles
- dispute incorrect reports
- correct stale postings

These workflows are planned; APIs are not implemented yet.

## Moderator responsibilities

Moderators review evidence quality, redact sensitive personal data, and mark reports as reviewed when support is sufficient. Moderators do not assign legal conclusions. Moderation tooling is future work.

## PII handling

Reports should reference posting URLs, public hiring content, and user-supplied timelines. Moderators remove unnecessary personal contact details for third parties when found in evidence.

## Escalation

High-risk abuse patterns should be escalated through private maintainer review and documented in issue tracker workflows.
