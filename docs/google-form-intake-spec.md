# Google Form Intake Specification

This document defines the Google Form fields for ghost-sweep public MVP report intake. The live Form URL is `https://forms.gle/PsjaYrbrCjAgZXjW8` (Batch G1A / 8A).

## Architecture

```text
Public site (GitHub Pages) --> Google Form --> Google Sheet --> manual review --> future backend import
```

Google Forms natively links responses to a Google Sheet. Maintainers review the Sheet manually. Approved records can later be imported into the PostgreSQL backend when hosted.

## Form title

Suggested: **ghost-sweep Community Report**

## Form description (recommended text)

Copy this into the Form description field:

```text
Submit a suspected ghost job for manual review by ghost-sweep maintainers.

Do not submit private personal data, credentials, or confidential documents.
Optional email is for follow-up only. Raw emails will not be published.
Submissions may be reviewed and moderated. Public data may be anonymized or summarized.
Publication is not guaranteed. False or abusive reports may be discarded.

This is an early public MVP. The full database-backed application is not hosted yet.
```

## Required fields

| # | Field label | Type | Required | Notes |
| - | ----------- | ---- | -------- | ----- |
| 1 | Job posting URL | Short answer | Yes | Full URL to the job listing |
| 2 | Company name | Short answer | Yes | As shown on the job board or employer site |
| 3 | Job title | Short answer | Yes | |
| 4 | Location or remote | Short answer | Yes | City, region, country, or "Remote" |
| 5 | Date seen | Date | Yes | When you observed the posting |
| 6 | Why do you suspect this is a ghost job? | Paragraph | Yes | Minimum 20 characters recommended in field help text |
| 7 | Has the company responded? | Multiple choice | Yes | Options: Yes / No / Unknown / Not applicable |
| 8 | Consent | Checkbox | Yes | Label below |

### Consent checkbox label

```text
I confirm this submission is made in good faith and is accurate to the best of my knowledge.
```

## Optional fields

| # | Field label | Type | Required | Notes |
| - | ----------- | ---- | -------- | ----- |
| 9 | Evidence links | Paragraph | No | URLs to repost history, public screenshots, archived listings |
| 10 | Optional contact email | Short answer | No | For follow-up only; never published raw |

## Field help text (recommended)

**Why do you suspect this is a ghost job?**

```text
Describe what you observed: reposted listing, no response after applying, long open duration, conflicting hire claims, etc. Minimum 20 characters.
```

**Evidence links**

```text
Link-only evidence for MVP. Do not upload confidential documents. File upload is deferred in the product.
```

**Optional contact email**

```text
Only provide if you want a follow-up. This email will not be published.
```

## Privacy and moderation wording

Include in the Form description or a dedicated section:

- Do not submit private personal data (government IDs, home addresses, phone numbers).
- Do not submit credentials, passwords, or confidential employer documents.
- Submissions may be reviewed and moderated before any public use.
- Optional email is for follow-up only.
- Public data may be anonymized or summarized.
- Raw applicant emails must not be published.

## Google Sheet setup

1. Create the Form at https://forms.google.com
2. Open **Responses** tab
3. Click the Google Sheets icon to create a linked spreadsheet
4. Restrict Sheet access to maintainers only
5. Add columns for review status if needed (e.g. `review_status`, `reviewer`, `notes`)

## Replacing the placeholder URL

Batch 8A (complete):

1. Public Send link: `https://forms.gle/PsjaYrbrCjAgZXjW8`
2. `public-mvp/index.html` contains two matching occurrences of the real URL
3. `python3.11 scripts/validate_public_mvp.py` rejects the placeholder and requires matching real Form URLs
4. GitHub Pages is still disabled; public launch not performed

## Data handling

| Data | Handling |
| ---- | -------- |
| Job URLs, company names, titles | Review for accuracy; may enter backend later |
| Optional email | Follow-up only; redact before any public summary |
| Evidence links | Verify publicly accessible; no confidential uploads |
| Consent | Required for intake; retain timestamp from Form response |

## Related documents

- [free-public-launch-plan.md](free-public-launch-plan.md)
- [public-launch-checklist.md](public-launch-checklist.md)
- [validation-artifacts.md](validation-artifacts.md)
- [SECURITY.md](../SECURITY.md)
