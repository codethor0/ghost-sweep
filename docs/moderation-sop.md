# Moderation SOP: Google Form and Sheet Review

Operational standard for manual moderation of public MVP report intake. This document supports [Issue #7](https://github.com/codethor0/ghost-sweep/issues/7). It is process documentation only; no backend import, moderation UI, or schema changes are implied.

## Scope

| In scope | Out of scope |
| -------- | ------------ |
| Google Form responses in the linked Sheet | In-app moderation UI |
| Maintainer triage and review states | Automated Sheet-to-PostgreSQL import (Issue #6) |
| Duplicate, spam, and decline handling | Evidence file upload |
| Email privacy and PII redaction | Legal determinations or public accusations |
| Import-readiness labeling for future batches | Scraping or auto-verification of job boards |

Architecture:

```text
GitHub Pages --> Google Form --> Google Sheet --> manual review (this SOP)
                                                      |
                                                      v
                                        future import (Batch 10D+ / Issue #6)
```

## Roles and access

| Role | Sheet access | Responsibilities |
| ---- | ------------ | ---------------- |
| Maintainer / moderator | Editor on project Sheet | Triage, set review states, redact PII, document decisions |
| Project account holder | Owner on Form and Sheet | Account recovery, sharing changes, escalation backup |
| Contributor | No Sheet access | Code and docs only unless granted moderator role |
| Public reporter | Form submit only | Submits via https://forms.gle/PsjaYrbrCjAgZXjW8 |

Sheet access must remain restricted to maintainers. Do not publish the Sheet URL. Do not share raw Form responses publicly.

## Sheet column conventions

Form responses populate native columns from [google-form-intake-spec.md](google-form-intake-spec.md). Maintainers add manual review columns to the right of Form fields.

### Form-derived columns (read-only from Form)

| Column | Source field | Notes |
| ------ | ------------ | ----- |
| Timestamp | Form auto | Submission time (UTC in Sheet) |
| Job posting URL | Required | Primary dedupe key |
| Company name | Required | As reported |
| Job title | Required | |
| Location or remote | Required | |
| Date seen | Required | Reporter observation date |
| Why do you suspect this is a ghost job? | Required | Narrative; minimum substance expected |
| Has the company responded? | Required | Yes / No / Unknown / Not applicable |
| Consent | Required | Must be checked |
| Evidence links | Optional | URL text only; no uploads in MVP |
| Optional contact email | Optional | Follow-up only; treat as sensitive |

### Maintainer review columns (manual)

Add these columns if not already present. Use exact header names for import planning consistency.

| Column | Type | Required when | Allowed values / format |
| ------ | ---- | ------------- | ----------------------- |
| `review_status` | enum | Always after first touch | See review states below |
| `reviewer` | text | When `review_status` is not `new` | Maintainer identifier (GitHub handle or project email) |
| `reviewed_at` | datetime | When `review_status` is not `new` | ISO 8601 or Sheet datetime |
| `decline_reason_code` | enum | When status starts with `declined_` or is `duplicate` / `spam` | See reason codes below |
| `duplicate_of` | text | When `decline_reason_code` is `duplicate` | Row number or canonical job posting URL |
| `notes` | text | Recommended always | Internal maintainer notes; never publish raw |
| `pii_redacted` | yes/no | Before any export or import | `yes` when email/PII removed or isolated |
| `import_ready` | yes/no | When `review_status` is `approved_for_import` | `yes` only when import checklist passes |
| `escalation_level` | enum | When escalated | `none`, `maintainer`, `lead` |

Do not rename Form response columns. Add new columns to the right only.

## Review states (`review_status`)

Use exactly one value per row.

| State | Meaning | Terminal | May set `import_ready=yes` |
| ----- | ------- | -------- | -------------------------- |
| `new` | Unreviewed Form response (default) | No | No |
| `in_review` | Claimed by a reviewer; triage in progress | No | No |
| `approved_for_import` | Passes moderation; eligible for future backend import | Yes | Yes (after checklist) |
| `declined_insufficient_evidence` | Narrative or links do not support review | Yes | No |
| `declined_not_ghost_job` | Report does not meet ghost-job criteria | Yes | No |
| `declined_duplicate` | Duplicate of an existing row or known posting | Yes | No |
| `declined_spam` | Bad faith, irrelevant, or abusive submission | Yes | No |
| `declined_pii` | Prohibited personal data; cannot be processed | Yes | No |
| `declined_other` | Other rejection; `notes` required | Yes | No |
| `escalated` | Needs senior maintainer or legal/privacy review | No | No |

State transitions:

```text
new --> in_review --> approved_for_import
                  --> declined_* (terminal)
                  --> escalated --> approved_for_import | declined_* 
new --> declined_spam (fast-path for obvious spam)
```

Only `approved_for_import` rows may have `import_ready=yes`. Backend import scripts (future) must ignore all other states.

Mapping to backend report states (future import only; not applied in Sheet today):

| Sheet `review_status` | Future backend `ReportStatus` (planned) |
| --------------------- | --------------------------------------- |
| `approved_for_import` | `pending` or `verified` (import batch decision) |
| `declined_*` | No import; row retained for audit |
| `escalated` | No import until resolved |

## Reviewer workflow

### 1. Intake (daily or twice weekly)

1. Open the project-linked Sheet (maintainers only).
2. Filter `review_status` = `new` or blank.
3. Sort by Timestamp ascending (oldest first).

### 2. Claim row

1. Set `review_status` = `in_review`.
2. Set `reviewer` and `reviewed_at`.
3. Do not edit Form-derived response cells.

### 3. Triage checklist

For each row, verify:

- [ ] Job posting URL is present and uses http or https
- [ ] URL is not a dangerous scheme (`javascript:`, `data:`, etc.)
- [ ] Company name and job title are present
- [ ] Narrative is at least 20 characters and good faith
- [ ] Consent checkbox is checked in Form data
- [ ] No prohibited PII in narrative or evidence (see privacy rules)
- [ ] Duplicate check performed (see duplicate rules)
- [ ] Evidence links, if any, are public and relevant

### 4. Decide outcome

| Outcome | Set `review_status` | Also set |
| ------- | ------------------- | -------- |
| Accept for future import | `approved_for_import` | Complete import-readiness checklist; `import_ready=yes` |
| Insufficient evidence | `declined_insufficient_evidence` | `decline_reason_code`, `notes` |
| Not a ghost job | `declined_not_ghost_job` | `decline_reason_code`, `notes` |
| Duplicate | `declined_duplicate` | `duplicate_of`, `decline_reason_code=duplicate` |
| Spam / abuse | `declined_spam` | `decline_reason_code=spam`, `notes` |
| Prohibited PII | `declined_pii` | `decline_reason_code=pii`, redact in `notes` summary only |
| Other decline | `declined_other` | `decline_reason_code=other`, `notes` (required) |
| Uncertain / high risk | `escalated` | `escalation_level`, `notes` |

### 5. Close review

1. Ensure `reviewer` and `reviewed_at` are set.
2. Never publish raw optional email or internal `notes`.
3. For approved rows, confirm `pii_redacted=yes` before any export.

Target SLA (best effort for MVP):

| Stage | Target |
| ----- | ------ |
| First touch (`new` to `in_review`) | 5 business days |
| Final decision | 10 business days |
| Escalated rows | 15 business days |

SLAs are operational goals, not public commitments, until a hosted product exists.

## Decline and duplicate reason codes

Use `decline_reason_code` for consistent reporting. One code per row.

| Code | Use when |
| ---- | -------- |
| `duplicate` | Same job posting URL or same company+title+location already reviewed |
| `spam` | Irrelevant content, test submissions, promotional abuse, bot-like patterns |
| `insufficient_evidence` | Narrative too vague; evidence links missing or unusable |
| `not_ghost_job` | Active hiring plausible; report does not meet ghost-job criteria |
| `pii` | Government ID, home address, phone, credentials, or third-party private data |
| `invalid_url` | Missing URL, malformed URL, or non-http(s) scheme |
| `no_consent` | Consent not checked (data integrity issue) |
| `other` | Any other decline; explain in `notes` |

For `declined_duplicate`, always set `duplicate_of` to the earlier row number (preferred) or canonical URL.

### Duplicate detection rules

1. Normalize job posting URL (trim, lowercase host, strip common tracking params mentally; full normalization in future import uses [job_url_validation.py](../backend/app/services/job_url_validation.py)).
2. Search Sheet for the same URL in prior approved or pending rows.
3. If same URL with materially same narrative within 30 days, mark `declined_duplicate`.
4. If same company + job title + location but different URL, set `escalated` for human judgment unless clearly the same repost.
5. Approved canonical row wins; later duplicates reference it in `duplicate_of`.

### Spam signals

- Nonsense or copy-paste filler in narrative
- Identical submissions from repeated patterns in short window
- URLs to unrelated sites
- Harassment or personal attacks on named individuals
- Submissions clearly testing the Form

Fast-path: set `review_status=declined_spam` without extended review when obvious.

## Evidence handling rules

MVP intake is **link-only**. There is no evidence file upload in the Form or product.

| Rule | Detail |
| ---- | ------ |
| Allowed | Public http/https URLs (job board listing, archive.org link, public social post) |
| Not allowed | Password-protected links, private Google Drive shares, confidential employer docs |
| Not allowed | Screenshots uploaded to Form (field is links only) |
| Verification | Moderator spot-checks that links resolve and support the narrative |
| Storage | Do not download and store reporter evidence in personal accounts |
| Future upload | Product evidence upload deferred; revisit when policy and storage exist |

If evidence links use dangerous schemes, set `review_status=declined_insufficient_evidence` with `decline_reason_code=invalid_url`.

Align with backend request validation (Batch 10B): only http/https URLs are accepted for employer evidence fields in the API. Sheet review should apply the same rule to optional Form evidence links.

## Email and privacy rules

| Data | Rule |
| ---- | ---- |
| Optional contact email | Follow-up only; **never publish raw** |
| Email in narrative | Redact in any export; prefer `declined_pii` if unrecoverable |
| Reporter identity | Do not publish without explicit consent beyond follow-up use |
| Third-party PII | Remove from any public summary; decline if necessary |
| `notes` column | Maintainers only; may contain redaction summaries, not raw PII |
| `pii_redacted` | Set `yes` before marking `import_ready=yes` |

Prohibited in Form submissions (decline or redact):

- Government IDs
- Home addresses
- Personal phone numbers
- Passwords or credentials
- Confidential employer documents
- Non-public personal data about third parties

For follow-up email: use project account only; do not CC public lists.

See also [legal-risk.md](legal-risk.md) and [SECURITY.md](../SECURITY.md).

## Escalation rules

Set `review_status=escalated` and `escalation_level` when:

| Condition | `escalation_level` | Action |
| --------- | ------------------ | ------ |
| Named individual harassment or defamation risk | `lead` | Private maintainer discussion; do not publish |
| Possible legal threat or takedown | `lead` | Route to security contact in SECURITY.md |
| Employer dispute of a high-visibility report | `maintainer` | Document in `notes`; no public statement |
| Ambiguous duplicate across companies | `maintainer` | Second reviewer required |
| PII spill in narrative | `maintainer` | Redact or decline; document outcome |
| Repeat submitter abuse pattern | `maintainer` | Consider Form filtering (manual, outside repo) |

Escalation resolution:

1. Second maintainer reviews within SLA.
2. Outcome recorded in `notes` with date and handles.
3. Final state must leave `escalated` (move to terminal or `approved_for_import`).
4. Open a private GitHub issue if product or policy change is needed.

Do not discuss escalated rows in public GitHub issues with raw submission content.

## Import-readiness conventions

Rows with `review_status=approved_for_import` may set `import_ready=yes` only when all checks pass:

| # | Check |
| - | ----- |
| 1 | Job posting URL valid http/https |
| 2 | Company name and job title non-empty |
| 3 | Narrative meets minimum quality (substantive ghost-job suspicion) |
| 4 | Consent recorded |
| 5 | `pii_redacted=yes` |
| 6 | No open escalation |
| 7 | `decline_reason_code` empty |
| 8 | `duplicate_of` empty |
| 9 | `notes` documents any judgment calls (optional but recommended) |

Future import pipeline (Issue #6) should:

- Import only rows where `import_ready=yes`
- Skip rows with any other `review_status`
- Never import optional email to public fields
- Normalize job URL via offline helper before dedupe
- Record Sheet row id and `reviewed_at` in import audit metadata

Full design: [sheet-import-design.md](sheet-import-design.md). Dry-run CLI: `python3.11 scripts/sheet_import_dry_run.py export.csv`. Implementation `--apply` deferred to Batch 12B.

## Audit trail expectations

| Event | Record location |
| ----- | --------------- |
| Form submission | Form Timestamp column (immutable) |
| Review claim and decision | Sheet `review_status`, `reviewer`, `reviewed_at`, `notes` |
| Decline reason | `decline_reason_code` + `notes` |
| Duplicate link | `duplicate_of` |
| Escalation | `escalation_level`, `notes`, private maintainer thread |
| Policy change | GitHub commit updating this SOP |
| Import (future) | Backend audit log + import batch id referencing Sheet row |

Rules:

- Do not delete Form response rows; use terminal decline states instead.
- Do not overwrite `reviewer` history silently; append context in `notes` with date if decision changes.
- Major decision reversals require second maintainer note in `notes`.
- Exporting Sheet data for backup: store in project-owned Drive only; restrict access.

Backend [audit logging](../backend/app/services/audit.py) applies to in-app actions only today. Sheet moderation audit is Sheet + this SOP until import bridges both systems.

## Product UI (future)

Issue #7 product milestones remain deferred:

- Moderation queue UI in frontend (admin)
- Bridge Sheet-approved rows to backend
- Evidence upload when policy allows

This SOP governs manual Sheet review until those ship.

## Related documents

- [google-form-intake-spec.md](google-form-intake-spec.md) — Form fields
- [moderation-model.md](moderation-model.md) — product moderation principles
- [post-launch-roadmap.md](post-launch-roadmap.md) — Tracks 1 and 2
- [sheet-import-design.md](sheet-import-design.md)
- [legal-risk.md](legal-risk.md) — legal and language risk
- [project-operations-plan.md](project-operations-plan.md) — project account ownership
- [audit-remediation-plan.md](audit-remediation-plan.md) — batch tracking
