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
| `pending` | Received; default on create; not publicly visible |
| `verified` | Moderator confirmed; eligible for public display and scoring |
| `dismissed` | Report rejected or insufficient; excluded from public APIs and scoring |
| `disputed` | Employer challenged the report; not publicly visible until verified |

New reports always start as `pending`. Public unauthenticated report APIs return only `verified` reports and omit internal reporter identifiers.

Score recalculation uses only `verified` reports. Pending report creation does not change public company or posting scores.

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
- public visibility limited to verified reports
- duplicate active report rejection per reporter, posting, and report type (`409` on conflict)
- report submission rate limiting separate from auth rate limits
- duplicate vote protection per user and report (`409` on conflict, including race-safe handling)
- duplicate employer response protection per employer user and report
- employer response rate scoring based on distinct eligible reports, not raw response rows
- refresh-token rotation and logout revocation
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

These workflows are planned; employer claim and response APIs are implemented. Full employer verification of company profiles remains future work.

## Moderator responsibilities

Moderators review evidence quality, redact sensitive personal data, and mark reports as reviewed when support is sufficient. Moderators do not assign legal conclusions. Moderation tooling is future work.

**Public MVP (Google Form / Sheet):** Manual review follows [moderation-sop.md](moderation-sop.md). In-app moderation APIs exist for local Docker use but are not wired to Form intake.

## PII handling

Reports should reference posting URLs, public hiring content, and user-supplied timelines. Moderators remove unnecessary personal contact details for third parties when found in evidence.

## Escalation

High-risk abuse patterns should be escalated through private maintainer review and documented in issue tracker workflows.
