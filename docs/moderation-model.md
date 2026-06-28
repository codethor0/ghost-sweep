# Moderation Model

ghost-sweep is evidence-based and community moderated. It is not a defamation platform.

## Report requirements

Every report must include:

- job posting URL
- company name
- job title
- timeline
- evidence
- report category

Reports without evidence are rejected.

## Report states

| State | Meaning |
| ----- | ------- |
| submitted | Received and awaiting review |
| reviewed | Moderator or trusted process reviewed evidence |
| disputed | Employer or reviewer challenged the report |

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

- authenticated submissions
- duplicate category checks per user and posting
- rate limiting on auth endpoints
- evidence requirement validation
- transparent scoring instead of accusatory labels

Future controls may include reputation thresholds, moderator queues, and employer verification workflows.

## Employer rights

Employers must be able to:

- claim a company profile
- respond to reports
- verify active roles
- dispute incorrect reports
- correct stale postings

## Moderator responsibilities

Moderators review evidence quality, redact sensitive personal data, and mark reports as reviewed when support is sufficient. Moderators do not assign legal conclusions.

## PII handling

Reports should reference posting URLs, public hiring content, and user-supplied timelines. Moderators remove unnecessary personal contact details for third parties when found in evidence.

## Escalation

High-risk abuse patterns should be escalated through private maintainer review and documented in issue tracker workflows.
