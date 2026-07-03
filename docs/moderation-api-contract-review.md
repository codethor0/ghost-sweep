# Moderation API Contract Review

## Status

Batch 14B docs-only. No API implementation. No backend behavior changes. No frontend changes. No deploy performed.

Baseline commit: `7087897` (main CI and Pages green before this batch).

## Current Baseline

| Layer | State |
| ----- | ----- |
| Public MVP intake | GitHub Pages + Google Form + manual Sheet moderation |
| Backend hosting | Local Docker only |
| Existing moderation APIs | Three admin endpoints on in-app `Report` records ([moderation-api.md](moderation-api.md)) |
| Moderation UI scope | Batch 13E — [moderation-ui-scope.md](moderation-ui-scope.md); not implemented |
| Offline Sheet Gates 11/12 | **ACCEPTED-MVP** (Section 18 amendment) |
| Live Sheet Gates 11/12 | **BLOCKED-LIVE** |
| `--apply` / production import | **Blocked** — not implemented |

Public Form intake does not create backend `Report` rows today. Backend moderation APIs operate on reports submitted through the in-app API (`POST /api/v1/reports`) against existing job postings.

## Existing Backend Moderation Contract

All routes are mounted under `/api/v1/moderation` ([backend/app/api/v1/moderation.py](../backend/app/api/v1/moderation.py)). Implementation: [backend/app/services/moderation.py](../backend/app/services/moderation.py).

### GET /api/v1/moderation/reports

| Aspect | Detail |
| ------ | ------ |
| Purpose | Paginated moderation queue filtered by report status |
| Auth | Bearer JWT; caller must have `is_admin = true` (`require_admin`) |
| Query params | `status` (default `pending`): `pending`, `verified`, `dismissed`, `disputed`; `page` (default 1); `page_size` (default 20, max 100) |
| Request body | None |
| Response `200` | `ReportListResponse`: `items[]`, `total`, `page`, `page_size` |
| Response item shape | `ReportResponse`: `id`, `job_posting_id`, `reporter_id`, `report_type`, `description`, `status`, `confidence_score`, `verification_votes`, `created_at`, `updated_at` |
| State transition | None (read-only) |
| Audit | None |
| Errors | `401` unauthenticated; `403` non-admin |
| Tests | `test_moderation_list_requires_admin`, `test_moderation_list_returns_pending_reports` in [test_moderation.py](../backend/tests/test_moderation.py) |

Ordering: oldest first (`created_at asc`).

### POST /api/v1/moderation/reports/{report_id}/verify

| Aspect | Detail |
| ------ | ------ |
| Purpose | Mark a report as verified after admin review |
| Auth | Bearer JWT; `is_admin = true` |
| Request body | None |
| Response `200` | Updated `ReportResponse` with `status = verified` |
| Allowed transitions | `pending` → `verified`; `disputed` → `verified` |
| Side effects | Recalculates job posting and company scores; inserts score snapshots; audit log `report.verified` |
| Audit metadata | `job_posting_id`, `previous_status`, `new_status: verified`; `actor_user_id` on audit row |
| Errors | `401`, `403`, `404` not found, `422` invalid transition |
| Tests | `test_verify_report_updates_status`, dispute re-verify, invalid transition, audit log, score snapshot tests |

Terminal: verified reports can become `disputed` via employer response API (not moderation route).

### POST /api/v1/moderation/reports/{report_id}/dismiss

| Aspect | Detail |
| ------ | ------ |
| Purpose | Dismiss a report after admin review |
| Auth | Bearer JWT; `is_admin = true` |
| Request body | Optional `DismissReportRequest`: `{ "reason": "..." }` (max 2000 chars); reason stored in audit metadata only, not on `Report` model |
| Response `200` | Updated `ReportResponse` with `status = dismissed` |
| Allowed transitions | `pending` → `dismissed`; `disputed` → `dismissed` |
| Side effects | Score recalculation; score snapshots; audit log `report.dismissed` with optional `reason` in metadata |
| Errors | `401`, `403`, `404`, `422` |
| Tests | Dismiss with/without reason, audit log, invalid transitions, terminal state |

Dismissed is terminal in Batch 6 — cannot reopen via moderation API.

### Related non-moderation endpoints (context only)

These exist but are **not** moderation-namespace routes:

| Method | Path | Notes |
| ------ | ---- | ----- |
| POST | `/api/v1/reports` | Creates report with `status = pending`; requires auth |
| GET | `/api/v1/reports/{report_id}` | Report detail; not admin-gated in current API |
| GET | `/api/v1/reports` | List by `job_posting_id`; not moderation queue |

No `GET /api/v1/moderation/reports/{id}` exists today.

## Existing Backend State Model

Defined in [backend/app/models/enums.py](../backend/app/models/enums.py) as `ReportStatus`:

| Status | Meaning |
| ------ | ------- |
| `pending` | Default on create; awaiting moderation |
| `verified` | Admin confirmed the report |
| `dismissed` | Admin rejected or found insufficient; terminal |
| `disputed` | Employer challenged the report; can return to verified or dismissed |

`Report` model fields ([backend/app/models/report.py](../backend/app/models/report.py)): `job_posting_id`, `reporter_id`, `report_type`, `description`, `status`, `confidence_score`, `verification_votes`, timestamps. No Sheet SOP columns.

### Important distinctions

- Backend `status` is **not** Sheet `review_status`. They are separate state machines.
- Backend `verified` is **not** Sheet `approved_for_import`. Sheet approval means import-eligible; backend verify means in-app moderation confirmed.
- Backend `dismissed` is **not** automatically mapped to a Sheet `declined_*` value unless a future bridge defines that mapping.
- Imported Sheet rows enter backend as `pending` per [sheet-import-design.md](sheet-import-design.md); Sheet approval does not auto-verify.

Employer dispute path: `pending` or `verified` → `disputed` via employer response service ([employer_responses.py](../backend/app/services/employer_responses.py)).

## Existing Sheet SOP Contract

Maintainer columns from [moderation-sop.md](moderation-sop.md), validated in [sheet_import.py](../backend/app/services/sheet_import.py) for import eligibility:

| Field | Meaning |
| ----- | ------- |
| `review_status` | Primary workflow state (`new`, `in_review`, `approved_for_import`, `declined_*`, `escalated`) |
| `reviewer` | Maintainer identifier when reviewed |
| `reviewed_at` | Review timestamp |
| `decline_reason_code` | Enum for declines; must be empty for import |
| `duplicate_of` | Row number or canonical URL for duplicates |
| `notes` | Internal maintainer notes |
| `pii_redacted` | `yes` required before import |
| `import_ready` | `yes` only when full checklist passes |
| `escalation_level` | `none`, `maintainer`, `lead` |

Form-derived fields (read-only from Form): job URL, company, title, location, date seen, narrative, company response, consent, evidence links, optional contact email.

### Sheet import eligibility rules (dry-run / future import)

From `check_eligibility` in [sheet_import.py](../backend/app/services/sheet_import.py):

1. `review_status` = `approved_for_import`
2. `import_ready` = `yes`
3. `pii_redacted` = `yes`
4. `decline_reason_code` empty
5. `duplicate_of` empty
6. `escalation_level` = `none` or empty
7. Consent checked
8. Required Form fields present and valid (URL http/https, company name length, etc.)

`--apply` remains blocked. Production import automation not enabled.

## Contract Gap Analysis

| Capability | Backend today | Sheet SOP today | Needed by moderation UI | Implementation gap | Risk |
| ---------- | ------------- | --------------- | ------------------------- | ------------------ | ---- |
| Queue list | Partial — GET list by `ReportStatus` only | Manual filter in Sheet | Yes | No Sheet queue API; no unified queue | Medium — dual systems |
| Report/submission detail | Partial — GET `/api/v1/reports/{id}` (non-admin) | Row view in Sheet | Yes | No moderation detail with Form fields; no admin detail route | Medium |
| Verify report | Yes — POST verify | N/A (uses `approved_for_import`) | Yes (in-app path) | Sheet path has no verify endpoint | Low for in-app; High for Sheet bridge |
| Dismiss report | Yes — POST dismiss with optional reason | Manual `declined_*` states | Yes | No structured decline codes on backend | Medium |
| `review_status` | No | Yes | Yes | Not on `Report` model | High — schema or bridge required |
| Reviewer identity | Audit `actor_user_id` only | `reviewer` column | Yes | No reviewer field on report; audit not exposed via API | Medium |
| `reviewed_at` | `updated_at` only (implicit) | Yes | Yes | No dedicated reviewed timestamp | Low |
| Decline reason | Optional free-text in audit metadata | `decline_reason_code` enum | Yes | No enum on backend; not in API response | Medium |
| Duplicate link | No | `duplicate_of` | Yes | No backend field or search API | High |
| Internal notes | Dismiss reason in audit only | `notes` column | Yes | No notes field on report | Medium |
| PII redaction flag | No | `pii_redacted` | Yes | Not on backend | High for import path |
| Import-ready flag | No | `import_ready` | Yes | Not on backend; dry-run only | High |
| Escalation level | No | Yes | Yes | Not on backend | Medium |
| Audit/history retrieval | Written to `audit_logs` table | Sheet + SOP | Yes | No GET audit API | Medium |
| Consent visibility | No (Sheet/Form only) | Form column | Yes | Not in backend until import | Medium |
| Optional contact email masking | No | Form column | Yes | Not in backend; PII risk if imported raw | High |
| Role-based access control | `is_admin` boolean only | Sheet Editor role | Yes | No moderator vs admin distinction | Medium before public deploy |

## Proposed Future API Contract

**All endpoints below marked PROPOSED — not implemented** unless noted as existing above.

### GET /api/v1/moderation/reports — EXISTING

See existing contract. Future enhancements (proposed): filter by date range, search by URL fragment, include job posting summary in list items.

### GET /api/v1/moderation/reports/{id} — PROPOSED

| Aspect | Detail |
| ------ | ------ |
| Purpose | Admin detail view for one report with job posting context |
| Auth | Admin JWT |
| Response | Extended report DTO: report fields + nested job posting URL/title/company + optional Sheet-origin metadata if bridged |
| Validation | UUID report id |
| Safety | Do not expose reporter PII beyond existing `reporter_id`; mask optional email if Sheet fields added |
| Schema change | Likely — extended response DTO; possible join fields |

### PATCH /api/v1/moderation/reports/{id}/review — PROPOSED

| Aspect | Detail |
| ------ | ------ |
| Purpose | Update Sheet-equivalent moderation fields on a report or linked intake record |
| Request body | `{ "review_status", "reviewer", "notes", "decline_reason_code", "duplicate_of", "pii_redacted", "import_ready", "escalation_level" }` (subset allowed) |
| Auth | Admin JWT |
| Validation | State machine rules from SOP; decline requires code; duplicate requires `duplicate_of`; import_ready gate |
| Safety | `import_ready=yes` blocked unless checklist passes; no `--apply` trigger |
| Schema change | **Likely required** if fields persist on backend |

### POST /api/v1/moderation/reports/{id}/verify — EXISTING

See existing contract.

### POST /api/v1/moderation/reports/{id}/dismiss — EXISTING

See existing contract. Proposed enhancement: accept structured `decline_reason_code` in addition to free-text reason.

### POST /api/v1/moderation/reports/{id}/duplicate — PROPOSED

| Aspect | Detail |
| ------ | ------ |
| Purpose | Mark report or intake as duplicate of another record |
| Request body | `{ "duplicate_of": "<uuid or sheet row or canonical url>" }` |
| Auth | Admin JWT |
| Validation | Target must exist; cannot duplicate self; sets terminal decline state |
| Schema change | Likely — `duplicate_of` reference field |

### POST /api/v1/moderation/reports/{id}/pii-redaction — PROPOSED

| Aspect | Detail |
| ------ | ------ |
| Purpose | Record PII review completion |
| Request body | `{ "pii_redacted": true, "notes": "..." }` |
| Auth | Admin JWT |
| Validation | Cannot set import_ready in same call without separate gate |
| Schema change | Likely |

### GET /api/v1/moderation/reports/{id}/audit — PROPOSED

| Aspect | Detail |
| ------ | ------ |
| Purpose | Retrieve audit history for a report |
| Auth | Admin JWT (auditor read-only role TBD) |
| Response | List of audit events: `action`, `actor_user_id`, `created_at`, `metadata_json` |
| Safety | Redact secrets; notes in metadata are internal |
| Schema change | Unlikely — reads existing `audit_logs` |

### GET /api/v1/moderation/duplicates/search — PROPOSED

| Aspect | Detail |
| ------ | ------ |
| Purpose | Find likely duplicates by normalized job URL or company+title |
| Query params | `url`, `company`, `title`, `location` |
| Auth | Admin JWT |
| Response | Ranked candidate matches |
| Validation | URL normalized via [job_url_validation.py](../backend/app/services/job_url_validation.py) |
| Schema change | Unlikely for search; may need index on normalized URL |

### Sheet bridge endpoints — PROPOSED (mode TBD)

If moderation UI operates on Sheet before backend intake:

- `GET /api/v1/moderation/intake` — list Form/Sheet rows (requires Google API integration; not designed)
- `PATCH /api/v1/moderation/intake/{row_id}` — update Sheet columns

These are **out of scope** for current backend and require separate security review. Batch 14B does not authorize Google API integration.

## Proposed State Mapping

| Sheet / UI concept | Backend `ReportStatus` | Mapping notes |
| ------------------ | ---------------------- | ------------- |
| `new` | N/A pre-import | No backend row until import or API create |
| `in_review` / `reviewing` | `pending` (loose) | Backend has no in-review substate; **ambiguous** |
| `approved_for_import` | `pending` after import | Sheet approval != verify; maintainer decision required |
| `declined_*` | `dismissed` (partial) | Multiple Sheet decline codes collapse to one backend status unless schema extended |
| `declined_duplicate` | `dismissed` + metadata | Requires `duplicate_of`; not on model today |
| `escalated` | `pending` (hold) | No backend escalation field; **ambiguous** |
| `needs_more_info` | None | Proposed UI-only; not in SOP |
| `verified` | `verified` | Direct match for in-app moderation |
| `dismissed` | `dismissed` | Direct match |
| `disputed` | `disputed` | Employer-driven; not Sheet-driven |

**Maintainer decisions required:**

1. Whether Sheet `approved_for_import` auto-maps to anything other than import-eligible `pending`.
2. Whether backend verify is required after Sheet-approved import.
3. Whether decline reason codes are stored on `Report` or audit-only.
4. Whether `needs_more_info` is added to SOP.

## Import Readiness Rules

Proposed server-side rules for future implementation (aligned with SOP and [moderation-ui-scope.md](moderation-ui-scope.md)):

1. `import_ready=yes` only if `review_status=approved_for_import`.
2. `pii_redacted=yes` required before `import_ready=yes`.
3. Valid consent required (Form field).
4. `duplicate_of` must be empty unless status is duplicate decline.
5. `decline_reason_code` required when status is any decline.
6. `escalation_level` default `none`; no import while escalated.
7. `notes` internal only — never in public API responses.
8. Optional contact email masked by default in UI and API list/detail.
9. Moderation UI must not expose or trigger `--apply`.
10. Production import remains a separate blocked batch with live gate requirements.

Dry-run parity: server validation should match [sheet_import.py](../backend/app/services/sheet_import.py) `check_eligibility`.

## Security and Privacy Requirements

1. **Admin-only access** — Current `require_admin`; extend to moderator role if split.
2. **RBAC before public deployment** — No public moderation endpoints on hosted backend without role review.
3. **Optional contact email** — Mask by default; reveal requires explicit moderator action with audit.
4. **Raw notes not public** — `notes` and dismiss reasons are internal/audit metadata.
5. **Audit reviewer and timestamp** — Every write records `actor_user_id` and audit row timestamp.
6. **No secrets in logs** — Audit metadata must not store tokens or credentials.
7. **No full raw row dumps** — API responses should field-scope Form data.
8. **URL safety** — http/https only; align with job URL validation and Batch 10B request validation.
9. **No automated import from UI** — `import_ready` is a label; `--apply` blocked.
10. **Rate limiting** — Auth endpoints rate-limited today; moderation writes need limits when exposed publicly.
11. **CORS** — Must be explicitly approved before hosted frontend calls moderation API.

## Testing Requirements

Future test coverage (beyond existing [test_moderation.py](../backend/tests/test_moderation.py)):

| Area | Tests |
| ---- | ----- |
| API auth | Non-admin 403 on all moderation routes (partially covered) |
| List queue | Pagination, status filters, empty queue |
| Detail endpoint | 404, admin 200, field presence |
| Review update | Valid/invalid state transitions; decline code required |
| Duplicate | `duplicate_of` required; search returns candidates |
| PII / import gates | `import_ready` rejected without `pii_redacted`; consent gate |
| Audit retrieval | Verify/dismiss/review writes audit rows; GET returns history |
| Email masking | Optional email absent from list; reveal endpoint audited |
| No apply path | No route triggers database import or `--apply` |
| Sheet parity | Eligibility rules match dry-run for bridged fields |

Existing tests cover: admin ACL, list pending, verify, dismiss, audit log creation, score snapshots, invalid transitions, dismissed terminal state.

## Implementation Boundaries

- **No implementation in Batch 14B.**
- Future API work requires maintainer approval and API contract sign-off.
- Persisting Sheet SOP fields on backend likely requires **schema migration** and Alembic review.
- Frontend wireframe/spec (Batch 14C) should precede UI implementation.
- Staging deployment requires separate infra approval ([render-deployment-plan.md](render-deployment-plan.md)).
- Live Sheet Gates 11/12 remain **BLOCKED-LIVE** and separate from moderation API work.
- `--apply` and production import remain **blocked**.

## Open Questions

1. Should the backend `Report` model absorb Sheet SOP fields, or should a separate `IntakeSubmission` entity exist?
2. Should Google Sheet remain source of truth for public MVP moderation until hosted intake exists?
3. Should the moderation UI target backend DB only, Sheet only, or bridge mode?
4. What is the canonical allowed set of `decline_reason_code` values in API (match SOP exactly)?
5. How should `duplicate_of` be represented — UUID, Sheet row number, normalized URL, or polymorphic reference?
6. What audit log retention and export policy is required?
7. What roles are needed beyond binary `is_admin` (moderator, lead, auditor)?
8. Should optional contact email ever be shown unmasked, and under what audit conditions?
9. What is the first implementation target environment — local Docker, Render staging, or production?
10. Should PATCH review replace POST verify/dismiss or coexist for in-app reports?

## Recommended Next Batches

| Batch | Scope | Type |
| ----- | ----- | ---- |
| **14C** | Moderation UI wireframe / interaction spec | Docs-only |
| **14D** | Moderation schema decision record (Report vs IntakeSubmission) | Docs-only |
| **14E** | Moderation API implementation plan (endpoint rollout order) | Docs-only |
| **14A** | Render staging implementation | Deploy — explicit infra approval only |

**Next recommended batch:** **14C** — moderation UI wireframe/spec (docs-only).

## Related Documents

- [moderation-ui-scope.md](moderation-ui-scope.md) — Batch 13E UI scope
- [moderation-api.md](moderation-api.md) — existing API reference
- [moderation-sop.md](moderation-sop.md) — Sheet workflow
- [moderation-model.md](moderation-model.md) — product principles
- [sheet-import-design.md](sheet-import-design.md) — import field mapping
- [sheet-import-apply-design.md](sheet-import-apply-design.md) — `--apply` gates (blocked)
