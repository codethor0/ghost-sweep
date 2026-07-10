# Reporting and Moderation Policy

This document describes how ghost-sweep handles suspected ghost job reports today and the standards that apply to community participation.

## Purpose

Ghost Sweep helps job seekers report and review **suspected ghost job postings** using structured intake, human moderation, and documented integrity workflows.

The project distinguishes:

- **Suspected ghost job** — a good-faith allegation based on available evidence
- **Community report** — a submission from a job seeker or contributor
- **Unverified submission** — intake that has not completed moderation
- **Moderated report** — a submission that has passed maintainer review under the current workflow

Do not represent an allegation as an established fact without sufficient review.

## Good-faith reporting

Reporters must confirm that:

- The submission is made in good faith
- Information is accurate to the best of their knowledge
- The report does not contain harassment, threats, or knowingly false claims

The public Google Form includes a consent checkbox. Maintainers may decline submissions that fail consent or good-faith requirements.

## Privacy

The following must **not** be disclosed publicly without explicit permission and maintainer review:

- Personal email addresses (except where the reporter explicitly consents to limited follow-up contact through the Form)
- Phone numbers
- Home addresses
- Recruiter personal information beyond what is necessary for a job posting allegation
- Credentials or account secrets
- Private correspondence
- Confidential documents
- Internal moderation notes
- Raw Google Sheet rows or exports

Optional contact email collected through the Form is for follow-up only. Raw emails must not be published in the repository, issues, pull requests, or public site content.

## Evidence and moderation

- A lack of employer response alone does **not** conclusively prove a ghost job.
- Reports should include relevant dates, links, and factual context when available.
- Submissions may be declined, marked as duplicates, escalated, or held for more information.
- Community reports remain **unverified** until moderation is complete under the current workflow.
- No automatic public accusation should be generated from an unreviewed submission.
- Employers and affected parties should use documented correction or appeal channels as those become available in product workflows.
- Moderators may remove or decline reports that are inaccurate, unsupported, abusive, unsafe, or legally problematic.

See [moderation-sop.md](moderation-sop.md) for maintainer Sheet workflow details.

## Current technical boundary

| Layer | Status |
| ----- | ------ |
| Public MVP | GitHub Pages static site at https://codethor0.github.io/ghost-sweep/ |
| Report intake | Google Form linked from the public site |
| Moderation | Manual Google Sheet workflow per [moderation-sop.md](moderation-sop.md) |
| Full backend | Local Docker only; not publicly hosted |
| Production Sheet import automation | **Not enabled** |
| Live Gate 11 / 12 | **BLOCKED-LIVE** unless real live-export verification has passed |
| `--apply` | **Not implemented**; blocked without maintainer approval |
| Private submission data | **Not** part of the open-source repository |

Open-sourcing the code does not make private Form or Sheet submission data public.

## Contributor boundary

Contributors must not:

- Commit downloaded Sheet exports or Form response CSVs
- Include private reporter contact information in issues or pull requests
- Implement `--apply` or production import automation without explicit maintainer approval
- Change Live Gate status without real live-export proof

Approved test fixtures (for example `backend/tests/fixtures/sheet_import_sample.csv`) are synthetic samples only and must not contain live submission data.

## Related documents

- [google-form-intake-spec.md](google-form-intake-spec.md)
- [moderation-sop.md](moderation-sop.md)
- [sheet-import-design.md](sheet-import-design.md)
- [sheet-import-apply-design.md](sheet-import-apply-design.md)
- [GOVERNANCE.md](../GOVERNANCE.md)
- [SECURITY.md](../SECURITY.md)
