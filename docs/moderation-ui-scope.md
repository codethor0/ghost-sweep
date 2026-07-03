# Moderation UI Scope

## Status

Batch 13E docs-only. No UI implemented. No backend changes. No deploy performed.

Baseline commit: `837175d` (PR #9 merged; main CI and Pages green as of Batch 13I).

## Current Intake Model

| Layer | State |
| ----- | ----- |
| Public site | GitHub Pages static MVP at https://codethor0.github.io/ghost-sweep/ |
| Report intake | Google Form (`https://forms.gle/PsjaYrbrCjAgZXjW8`) |
| Moderation queue | Google Sheet — manual review per [moderation-sop.md](moderation-sop.md) |
| Full backend | Local Docker only (FastAPI, PostgreSQL, Redis, Next.js) |
| Production import automation | **Not enabled** |
| `--apply` mode | **Blocked** — not implemented |
| Offline Sheet Gates 11/12 | **ACCEPTED-MVP** (Section 18 amendment, Batch 12S) |
| Live Sheet Gates 11/12 | **BLOCKED-LIVE** |
| In-app moderation APIs | Exist for backend `Report` records; not wired to Form/Sheet intake |

Architecture today:

```text
GitHub Pages --> Google Form --> Google Sheet --> manual moderation (SOP)
                                                      |
                                                      v
                                        future import --> PostgreSQL (blocked)
```

Render deployment planning ([render-deployment-plan.md](render-deployment-plan.md)) is docs-only and does not authorize deployment.

## Problem Statement

Manual Sheet moderation works for MVP but does not scale and carries operational risk:

1. **Sheet dependency** — Maintainers must use a restricted Google Sheet with no structured audit trail tied to the backend.
2. **Inconsistent decisions** — Review states, decline codes, and import-readiness depend on column discipline without UI validation.
3. **PII exposure risk** — Optional contact email and narrative PII are easy to mishandle without guided redaction workflows.
4. **Duplicate handling** — URL and company/title/location dedupe is manual with no search or match suggestions.
5. **Hosted backend gap** — When a staging or production backend exists, moderators need a product surface that bridges Sheet intake and in-app reports without bypassing human review.
6. **Audit and accountability** — Sheet edits lack the structured audit events that backend [audit logging](../backend/app/services/audit.py) provides for in-app actions.

A future moderation UI should reduce Sheet dependency over time, standardize review decisions, protect privacy, and prepare for hosted workflows while keeping human review in the loop.

## Non-Goals

- No UI implementation in Batch 13E
- No backend implementation or schema changes
- No production import or `--apply` mode
- No live Sheet gate reopening or amendment
- No automated publishing of moderated content
- No cloud deploy, Render resources, or GitHub Pages changes
- No Google Form or Sheet changes
- No evidence file upload in MVP UI scope
- No legal determinations or public accusatory labels

## Moderation Roles

| Role | Access today | Future UI expectation |
| ---- | ------------ | --------------------- |
| Anonymous reporter | Form submit only | Unchanged for public MVP; future in-app report may require auth |
| Moderator | Sheet Editor (maintainers) | Review queue, PII review, duplicate check, approve/decline |
| Maintainer / admin | Sheet Owner + backend `is_admin` | Same as moderator plus escalation resolution, settings |
| Auditor / read-only reviewer | Not defined | Optional future role: view queue and audit history without decision actions |

**Auth details: TBD.** Backend moderation APIs today require a bearer JWT for a user with `is_admin = true` ([moderation-api.md](moderation-api.md)). How moderators authenticate in a product UI (email/password, SSO, maintainer-provisioned accounts) is not decided.

## Moderation Workflow

Intended end-to-end flow for a future moderation UI (aligned with [moderation-sop.md](moderation-sop.md)):

1. **Intake received** — Form submission lands in Sheet (current) or future API intake record.
2. **Item enters review queue** — Row with `review_status` = `new` or blank appears in queue; backend equivalent is `Report.status` = `pending` after import.
3. **Moderator opens item** — Claim row: set `in_review`, `reviewer`, `reviewed_at`.
4. **PII review** — Scan narrative, optional email, evidence links; redact or decline if prohibited data present.
5. **Duplicate review** — Search normalized job URL and company/title/location; link `duplicate_of` if match.
6. **Evidence review** — Spot-check http/https evidence links; reject dangerous schemes.
7. **Decision** — One terminal or progressing state:
   - `approved_for_import` — eligible for future import (Sheet) or verify (in-app)
   - `in_review` / `reviewing` — work in progress
   - `declined_*` — terminal decline with reason code
   - `declined_duplicate` / `duplicate` — terminal with `duplicate_of`
   - `escalated` — needs senior review
   - `needs_more_info` — **proposed** optional state if product adds reporter follow-up; not in SOP today
8. **Optional escalation** — Set `escalation_level` (`maintainer`, `lead`); resolve to approve or decline.
9. **Audit trail captured** — Reviewer identity, timestamp, decision, reason, notes (internal).
10. **Future import remains separate** — `import_ready=yes` does not trigger import; `--apply` and production automation stay blocked until explicit maintainer approval and live gate resolution.

### Sheet vs backend state mapping

Sheet moderation (Form intake) and in-app moderation (PostgreSQL `Report`) use different state machines today:

| Sheet `review_status` | Meaning | Backend `ReportStatus` (after import) |
| --------------------- | ------- | ------------------------------------- |
| `new`, `in_review` | Pre-import triage | N/A until imported |
| `approved_for_import` | Import-eligible | Imports as `pending` (not auto-verified) |
| `declined_*` | Terminal; no import | N/A |
| `escalated` | Blocked until resolved | N/A |

In-app API transitions ([moderation-api.md](moderation-api.md)): `pending` / `disputed` → `verified` or `dismissed`.

A future UI must not conflate Sheet approval with backend verification without explicit product rules.

## Moderation State Model

Fields from [moderation-sop.md](moderation-sop.md) maintainer columns. These exist in Sheet workflow and in [sheet_import.py](../backend/app/services/sheet_import.py) eligibility checks; they are **not** columns on the backend `Report` model today.

| Field | Type | Meaning |
| ----- | ---- | ------- |
| `review_status` | enum | Primary workflow state (see SOP for full list) |
| `reviewer` | text | Maintainer identifier (GitHub handle or project email) |
| `reviewed_at` | datetime | ISO 8601 when review started or decided |
| `decline_reason_code` | enum | Required for declines; must be empty for import |
| `duplicate_of` | text | Row number or canonical URL when duplicate |
| `notes` | text | Internal maintainer notes; never public |
| `pii_redacted` | yes/no | `yes` required before import |
| `import_ready` | yes/no | `yes` only when full import checklist passes |
| `escalation_level` | enum | `none`, `maintainer`, `lead` |

### Import-ready checklist (all required for `import_ready=yes`)

Per SOP and sheet import dry-run:

1. `review_status` = `approved_for_import`
2. Consent checked on Form row
3. Job posting URL present and valid http/https
4. Required Form fields populated
5. `pii_redacted` = `yes`
6. No open escalation (`escalation_level` = `none` or empty)
7. `decline_reason_code` empty
8. `duplicate_of` empty
9. Narrative meets minimum substance (moderator judgment)

Backend `Report` model fields today: `job_posting_id`, `reporter_id`, `report_type`, `description`, `status` (`pending` | `verified` | `dismissed` | `disputed`), `confidence_score`, timestamps. No Sheet moderation columns on the model.

## UI Screens

Future screens only — not implemented.

### 1. Login / session

| Aspect | Detail |
| ------ | ------ |
| Purpose | Authenticate moderators for admin API access |
| Required data | Credentials or SSO token; session with role claims |
| Actions | Sign in, sign out, session refresh |
| Safety | No shared accounts; rate limit auth; no secrets in client storage beyond short-lived tokens |

**TBD:** Auth provider, refresh-token UX (frontend does not persist refresh tokens today).

### 2. Review queue

| Aspect | Detail |
| ------ | ------ |
| Purpose | List items awaiting moderation, oldest first |
| Required data | Filter by status (`new`, `in_review`, `escalated`); pagination; sort by timestamp |
| Actions | Open item, claim (`in_review`), filter, search by URL/company |
| Safety | Admin/moderator role only; no public access; do not expose optional contact email in list view by default |

**Data source TBD:** Sheet API bridge vs backend queue after import vs hybrid.

### 3. Submission detail

| Aspect | Detail |
| ------ | ------ |
| Purpose | Full view of one intake record |
| Required data | Form fields: URL, company, title, location, date seen, narrative, company response, consent, evidence links; moderation fields |
| Actions | Navigate to PII, duplicate, evidence, decision panels |
| Safety | Mask optional email by default (click-to-reveal with audit log); warn on dangerous URL schemes |

### 4. PII redaction panel

| Aspect | Detail |
| ------ | ------ |
| Purpose | Guide moderator through PII check before approval |
| Required data | Narrative, email field, evidence text; `pii_redacted` flag |
| Actions | Mark `pii_redacted=yes`, decline with `decline_reason_code=pii`, add internal note |
| Safety | Cannot set `import_ready=yes` unless `pii_redacted=yes`; no export of raw email |

### 5. Duplicate matching panel

| Aspect | Detail |
| ------ | ------ |
| Purpose | Surface likely duplicates before approval |
| Required data | Normalized job URL; search results (Sheet rows or backend postings/reports) |
| Actions | Set `duplicate_of`, decline as duplicate, override with note if false positive |
| Safety | Require `duplicate_of` when declining as duplicate; canonical row wins per SOP |

**TBD:** Exact matching algorithm UI (offline normalization via [job_url_validation.py](../backend/app/services/job_url_validation.py) exists; no duplicate-search API).

### 6. Decision panel

| Aspect | Detail |
| ------ | ------ |
| Purpose | Apply terminal or progressing review decision |
| Required data | Current `review_status`; eligible transitions |
| Actions | Approve for import, decline (with reason), escalate, return to `in_review` |
| Safety | Decline requires `decline_reason_code`; approve requires consent + PII checklist; confirm dialog for approve; no single-click import |

For in-app reports: verify / dismiss maps to backend API (existing).

### 7. Audit / history panel

| Aspect | Detail |
| ------ | ------ |
| Purpose | Show who changed what and when |
| Required data | Event type, actor, timestamp, previous/new status, reason/metadata |
| Actions | Read-only view; filter by submission |
| Safety | Internal notes never shown on public surfaces; align with backend audit log where available |

Backend audit events today: `report.verified`, `report.dismissed` with optional reason in metadata. Sheet history is revision history + SOP discipline until bridged.

### 8. Admin / settings (optional)

| Aspect | Detail |
| ------ | ------ |
| Purpose | Moderator roster, SLA display, decline code reference |
| Required data | Role list, SOP constants |
| Actions | View-only in v1; user provisioning TBD |
| Safety | Maintainer-only; no public settings |

## API Assumptions

### Confirmed existing (backend, local Docker)

Documented in [moderation-api.md](moderation-api.md); implemented in [backend/app/api/v1/moderation.py](../backend/app/api/v1/moderation.py):

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/api/v1/moderation/reports` | Paginated queue by `ReportStatus` (`pending`, `verified`, `dismissed`, `disputed`) |
| POST | `/api/v1/moderation/reports/{report_id}/verify` | `pending`/`disputed` → `verified`; recalculates scores; audit log |
| POST | `/api/v1/moderation/reports/{report_id}/dismiss` | `pending`/`disputed` → `dismissed`; optional `reason` in body; audit log |

Auth: Bearer JWT; caller must have `is_admin = true`. Errors: 401, 403, 404, 422.

These APIs operate on **backend Report records**, not Google Sheet rows. They do not expose Sheet moderation columns (`review_status`, `import_ready`, etc.).

### Proposed future APIs (not implemented)

Mark all as **proposed** until design approval and implementation:

| Proposed API | Purpose |
| ------------ | ------- |
| List Form/Sheet intake queue | Bridge or replace Sheet for pre-import items |
| Get submission detail (Sheet-shaped) | Full Form + moderation fields for one row |
| Update moderation decision (Sheet-shaped) | Set `review_status`, reason codes, `duplicate_of`, notes |
| Mark PII redacted | Set `pii_redacted` with validation |
| Set import ready | Set `import_ready` only when checklist passes (server-side validation) |
| Duplicate search | Normalized URL / fuzzy company+title lookup |
| Audit log retrieval | List events for submission or report |
| Form intake webhook / POST | Future replacement for Google Form (out of MVP scope) |

Sheet import dry-run logic in [sheet_import.py](../backend/app/services/sheet_import.py) encodes eligibility rules server-side for CSV rows; a future API could reuse that validation for UI feedback.

Frontend today: no moderation routes. [DashboardPanel.tsx](../frontend/components/dashboard/DashboardPanel.tsx) states moderation tools are not wired.

## Safety and Privacy Requirements

1. **Optional contact email** — Hidden by default in list and detail views; reveal requires moderator action; never publish raw.
2. **PII redaction** — `pii_redacted=yes` required before `import_ready=yes`; UI must block approval path until confirmed.
3. **Internal notes** — `notes` and dismissal reasons in audit metadata are not public API fields.
4. **No raw credentials** — No passwords, API keys, or session secrets in UI or logs.
5. **Audit reviewer and timestamp** — Every decision records actor and time (backend audit service pattern).
6. **No accidental approval** — Confirm step for approve/import-ready; consent must be valid.
7. **Import gate** — UI must not trigger `--apply` or database import; import_ready is a label only.
8. **Duplicate handling** — Declining as duplicate requires `duplicate_of`; prevent duplicate approvals for same normalized URL where detectable.
9. **Role-based access** — Moderation surfaces require admin/moderator role; 403 for others (existing ACL tested in [test_moderation.py](../backend/tests/test_moderation.py)).
10. **Rate limiting** — Auth endpoints rate-limited today; moderation write endpoints should be rate-limited when exposed publicly.
11. **Dangerous URLs** — Reject or flag `javascript:`, `file:`, `data:`, etc. (aligned with job URL validation and Batch 10B request validation).
12. **Evidence links only** — No file upload in MVP UI; link scheme validation only.

## Decision Rules

Proposed business rules for UI validation (aligned with SOP and sheet import):

| Rule | Requirement |
| ---- | ----------- |
| Approve for import | Form consent valid; narrative sufficient; evidence acceptable; PII addressed |
| Approve for import | `pii_redacted` = `yes` |
| `import_ready` = `yes` | Requires `review_status` = `approved_for_import` and full checklist |
| Decline | Requires `decline_reason_code` |
| Duplicate decline | Requires `duplicate_of` |
| Notes | Internal only; never exposed on public MVP or unauthenticated API |
| Escalation default | `escalation_level` = `none` or empty unless escalated |
| Backend verify | Separate from Sheet approve; only for imported `Report` in `pending`/`disputed` |
| Dismissed terminal | Backend dismissed reports cannot reopen via API (Batch 6) |

### Decline reason codes (from SOP)

`duplicate`, `spam`, `insufficient_evidence`, `not_ghost_job`, `pii`, `invalid_url`, `no_consent`, `other`

## Open Questions

1. **Auth provider** — Local email/password vs SSO vs maintainer-provisioned accounts only?
2. **Moderator identity source** — GitHub handle, project email, or backend `User` record?
3. **Sheet as temporary source** — Does UI read/write Sheet via API, or wait until Form intake moves to backend?
4. **Target environment** — Local Docker first, Render staging, or production later?
5. **Audit log schema** — Do Sheet moderation events need new backend tables before UI launch?
6. **Exact duplicate matching** — URL-only vs company+title+location fuzzy match thresholds?
7. **`needs_more_info` state** — Add to SOP or keep escalation-only?
8. **Bridge timing** — Moderation UI before or after `--apply` implementation approval?
9. **Public MVP coexistence** — How long Form + Sheet remain canonical intake after UI ships?

## Implementation Boundaries

Future implementation requires separate maintainer approval and dedicated batches. Each area needs its own gate:

| Area | Prerequisite |
| ---- | ------------ |
| API contract review | Map Sheet fields to API DTOs; no invented fields |
| Schema review | If persistence of Sheet moderation state in Postgres is required |
| Frontend routes | Admin-only layout; no public moderation URLs |
| Auth/session design | Align with [auth-api.md](auth-api.md); refresh token policy |
| Tests | API ACL, decision validation, PII gate, duplicate rules |
| Staging deploy | Render plan approval ([render-deployment-plan.md](render-deployment-plan.md)); not authorized by this doc |
| Security review | RBAC, rate limits, audit completeness |

Batch 13E does not authorize any of the above.

## Recommended Future Batches

Batch numbers 13F through 13I were consumed for GitHub health audits, PR #9 merge hygiene, and Pages rerun. Use the next available labels:

| Batch | Scope | Type |
| ----- | ----- | ---- |
| **14B** | Moderation API contract review — map Sheet SOP fields to proposed endpoints; docs-only | Docs |
| **14C** | Moderation UI wireframe / interaction spec — screen flows, empty states, error cases; docs-only | Docs |
| **14A** | Render staging implementation — only if maintainer explicitly approves infra ([render-deployment-plan.md](render-deployment-plan.md)) | Deploy |
| Later | Backend schema for intake bridge, frontend admin UI, Sheet API integration | Implementation — separate approval each |

**Next recommended batch after 13E:** **14B** — moderation API contract review (docs-only).

## Related Documents

- [moderation-sop.md](moderation-sop.md) — operational Sheet workflow
- [moderation-model.md](moderation-model.md) — product principles
- [moderation-api.md](moderation-api.md) — existing backend admin APIs
- [google-form-intake-spec.md](google-form-intake-spec.md) — Form fields
- [sheet-import-design.md](sheet-import-design.md) — import eligibility and field mapping
- [sheet-import-apply-design.md](sheet-import-apply-design.md) — `--apply` gates (blocked)
- [post-launch-roadmap.md](post-launch-roadmap.md) — Track 2 moderation workflow
- [render-deployment-plan.md](render-deployment-plan.md) — hosting plan (no deploy authorized)
