# Moderation Schema Decision Record

## Status

Batch 14D docs-only. No schema changes. No migrations. No backend behavior changes. No UI changes. No deploy performed.

Baseline commit: `ae6897f` (main CI and Pages green before this batch).

## Context

| Layer | State |
| ----- | ----- |
| Public MVP intake | GitHub Pages + Google Form + manual Sheet moderation |
| Backend hosting | Local Docker only |
| Sheet SOP fields | Richer than backend `ReportStatus` |
| Backend `ReportStatus` | `pending`, `verified`, `dismissed`, `disputed` |
| Planning artifacts | Batch 13E UI scope, 14B API contract review, 14C wireframe spec |
| Offline Sheet Gates 11/12 | **ACCEPTED-MVP** (Section 18 amendment) |
| Live Sheet Gates 11/12 | **BLOCKED-LIVE** |
| `--apply` / production import | **Blocked** |

No `IntakeSubmission`, `ModerationReview`, or Sheet SOP columns exist on the backend `Report` model today. Sheet eligibility rules live in offline [sheet_import.py](../backend/app/services/sheet_import.py) only.

## Problem

Future moderation UI and API (Batches 13E--14C) require durable representation of:

- `review_status`, `reviewer`, `reviewed_at`
- `decline_reason_code`, `duplicate_of`, `notes`
- `pii_redacted`, `import_ready`, `escalation_level`
- Form intake fields including optional contact email

The backend `Report` model does not carry these fields. Backend `verified` / `dismissed` are **not** equivalent to Sheet `approved_for_import` / `declined_*` / `duplicate`.

Specific gaps:

1. **State conflation risk** — Overloading `ReportStatus` with import workflow would confuse public scoring reports with pre-import intake rows.
2. **Import readiness** — Needs explicit, server-validated gates aligned with SOP and dry-run logic.
3. **Privacy** — Optional contact email and internal notes need schema-level separation from public report fields.
4. **Audit** — Moderation decisions need durable events; current `audit_logs` writes verify/dismiss only, with no retrieval API.
5. **Dual intake paths** — In-app reports (require existing `job_posting_id`) vs Form/Sheet rows (no backend row until import) need a clear domain boundary.

## Existing Backend State

### Report model ([backend/app/models/report.py](../backend/app/models/report.py))

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | Primary key |
| `job_posting_id` | UUID FK | Required; report tied to existing posting |
| `reporter_id` | UUID FK nullable | Authenticated reporter |
| `report_type` | enum | Report category |
| `description` | text | Min 20 chars on create |
| `status` | `ReportStatus` | Default `pending` |
| `confidence_score` | numeric | Scoring |
| `verification_votes` | int | Community votes |
| `created_at`, `updated_at` | timestamps | From mixin |

No Sheet SOP columns. No duplicate, PII, or import-ready fields.

### ReportStatus ([backend/app/models/enums.py](../backend/app/models/enums.py))

| Value | Meaning |
| ----- | ------- |
| `pending` | Default on create |
| `verified` | Admin confirmed |
| `dismissed` | Admin rejected; terminal |
| `disputed` | Employer challenged |

### Moderation endpoints ([backend/app/api/v1/moderation.py](../backend/app/api/v1/moderation.py))

| Method | Path | Behavior |
| ------ | ---- | -------- |
| GET | `/api/v1/moderation/reports` | Paginated by `ReportStatus`; admin only |
| POST | `/api/v1/moderation/reports/{id}/verify` | `pending`/`disputed` → `verified` |
| POST | `/api/v1/moderation/reports/{id}/dismiss` | Optional reason in audit metadata only |

### Audit behavior ([backend/app/services/audit.py](../backend/app/services/audit.py), [audit_log.py](../backend/app/models/audit_log.py))

- `AuditLog`: `actor_user_id`, `action`, `entity_type`, `entity_id`, `metadata` (JSONB), `created_at`
- Moderation writes: `report.verified`, `report.dismissed` with status metadata
- No GET audit API; no intake-specific events

### Tests ([backend/tests/test_moderation.py](../backend/tests/test_moderation.py))

Cover admin ACL, list, verify, dismiss, audit log creation, score snapshots, invalid transitions, terminal dismissed state.

### Migrations

Two Alembic revisions: `001_initial_uuid_schema`, `002_employer_claim_constraints`. No moderation intake tables.

## Existing Sheet SOP State

Maintainer columns from [moderation-sop.md](moderation-sop.md), validated in [sheet_import.py](../backend/app/services/sheet_import.py):

| Field | Purpose |
| ----- | ------- |
| `review_status` | Primary workflow state |
| `reviewer` | Maintainer identifier |
| `reviewed_at` | Review timestamp |
| `decline_reason_code` | Enum for declines |
| `duplicate_of` | Row number or canonical URL |
| `notes` | Internal maintainer notes |
| `pii_redacted` | `yes` before import |
| `import_ready` | `yes` when checklist passes |
| `escalation_level` | `none`, `maintainer`, `lead` |

SOP decline codes: `duplicate`, `spam`, `insufficient_evidence`, `not_ghost_job`, `pii`, `invalid_url`, `no_consent`, `other`.

SOP review states include: `new`, `in_review`, `approved_for_import`, `declined_*`, `escalated`.

### Import eligibility (dry-run; `--apply` blocked)

1. `review_status` = `approved_for_import`
2. `import_ready` = `yes`
3. `pii_redacted` = `yes`
4. `decline_reason_code` empty
5. `duplicate_of` empty
6. `escalation_level` none/empty
7. Consent checked
8. Required Form fields valid

## Decision Drivers

1. Preserve public MVP safety — no automated import or publish from schema design.
2. Do not conflate Sheet `review_status` with backend `ReportStatus`.
3. Make import readiness explicit, validated, and auditable.
4. Protect optional contact email and internal notes at the data model layer.
5. Support future moderation UI queue, detail, and decision panels (Batch 14C).
6. Support future API validation matching dry-run rules.
7. Keep migration path incremental — avoid big-bang Report redesign.
8. Avoid overbuilding before Render staging approval.
9. No live import automation; Live Gates 11/12 remain **BLOCKED-LIVE**.
10. Maintain human review before any future import.

## Options Considered

### Option 1: Add Sheet SOP fields directly to Report

**Description:** Add nullable columns on `reports` for all SOP fields.

| Aspect | Assessment |
| ------ | ---------- |
| Benefits | Simplest query path; one entity for UI detail |
| Drawbacks | Report requires `job_posting_id` today — Form rows have no posting until import; conflates intake with public report lifecycle; `verified` vs `approved_for_import` collision |
| Migration | Alter `reports`; nullable columns; backfill awkward for non-imported Sheet rows |
| API | Extend `ReportResponse`; overload verify/dismiss semantics |
| UI | Single detail view but misleading for pre-import intake |
| Privacy | Contact email on same table as public-facing report increases exposure risk |
| Testing | Many Report tests assume current shape; import gate tests mixed with scoring |

**Verdict:** Rejected — wrong lifecycle binding.

### Option 2: Create separate ModerationReview table linked to Report

**Description:** New `moderation_reviews` table with SOP fields FK to `reports.id`.

| Aspect | Assessment |
| ------ | ---------- |
| Benefits | Separates moderation workflow from report core fields |
| Drawbacks | Still assumes Report exists first; Form/Sheet intake has no Report until after import — chicken-and-egg |
| Migration | New table + FK; only helps in-app reports |
| API | PATCH review on report id |
| UI | Works for in-app path only |
| Privacy | Moderation fields isolated from report description |
| Testing | Clear split but incomplete for Sheet-first workflow |

**Verdict:** Insufficient alone for Form/Sheet intake.

### Option 3: Create separate IntakeSubmission model for Form/Sheet imports

**Description:** New `intake_submissions` for Form/Sheet row data; optional `moderation_reviews` 1:1 or embedded moderation columns on intake.

| Aspect | Assessment |
| ------ | ---------- |
| Benefits | Matches actual intake path; Report created only after import; clear staging object; aligns with [sheet-import-design.md](sheet-import-design.md) |
| Drawbacks | More tables; bridge from Sheet; duplicate domain with Report until import links them |
| Migration | New tables; indexes on queue fields; unique external id for Sheet row |
| API | Intake queue endpoints; separate from in-app moderation |
| UI | Queue shows intake rows; detail matches Batch 14C wireframe |
| Privacy | Contact email scoped to intake; never on Report by default |
| Testing | Dry-run rules map directly to intake + review entities |

**Verdict:** Preferred primary direction.

### Option 4: Keep Sheet as source of truth; bridge-only importer

**Description:** No intake tables; UI reads/writes Google Sheet via API; backend unchanged until `--apply`.

| Aspect | Assessment |
| ------ | ---------- |
| Benefits | No migration; Sheet remains canonical |
| Drawbacks | No hosted moderation UI without Google API integration; weak audit; privacy risk in Sheet API responses; does not support local Docker moderation UI goal |
| Migration | None |
| API | Google Sheets API (not in backend today) |
| UI | Dependent on external Sheet |
| Privacy | Sheet access control only |
| Testing | Hard to integration-test without live Google |

**Verdict:** Acceptable short-term operationally; insufficient for product moderation UI on backend.

## Recommended Direction

**Primary recommendation (planning-only):**

1. Introduce **`IntakeSubmission`** for Google Form / Sheet-import intake records (staging domain).
2. Introduce **`ModerationReview`** as a 1:1 table linked to `IntakeSubmission` (or embedded moderation columns on intake if audit needs stay minimal — see Open Questions).
3. Keep **`Report`** and **`ReportStatus`** as the in-app public/reporting domain; do not overload with import workflow state.
4. On future import (`--apply` when explicitly approved), create/link `job_posting` + `Report` with `status=pending`; store `intake_submission_id` reference for traceability.
5. Retain existing verify/dismiss moderation endpoints for in-app Reports until a unified moderation API is explicitly approved.
6. Extend **`audit_logs`** (or add **`moderation_audit_events`**) for intake moderation actions — prefer extending `audit_logs` with `entity_type=intake_submission` if metadata schema suffices.

**Rationale:** Separates intake/moderation/import staging from scored public reports; matches Sheet SOP and dry-run eligibility; reduces conflation of `verified` with `approved_for_import`; supports Batch 14C UI without forcing Form rows into Report prematurely.

## Proposed Future Data Model

**PROPOSED — NOT IMPLEMENTED.** Requires maintainer approval and Batch 14G migration plan before any code.

### IntakeSubmission

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | Primary key |
| `source` | enum | `google_form_sheet`, `manual_admin`, `future_api` |
| `source_external_id` | string nullable | Sheet row key, Form response id, or stable hash |
| `submitted_at` | timestamptz | Form timestamp |
| `job_posting_url` | text | Normalized on write (future) |
| `company_name` | string | |
| `job_title` | string | |
| `location_or_remote` | string | |
| `date_seen` | date | |
| `suspicion_reason` | text | Narrative |
| `company_response` | string | Form enum value |
| `consent` | boolean | Must be true for import |
| `evidence_links` | text nullable | Raw Form field |
| `optional_contact_email` | text nullable | **Masked in API**; encryption TBD |
| `imported_report_id` | UUID FK nullable | Set after successful `--apply` (future) |
| `created_at`, `updated_at` | timestamps | |

**Indexes (proposed):** `submitted_at`, `source_external_id` unique per source, normalized URL hash for duplicate search.

### ModerationReview

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | Primary key |
| `intake_submission_id` | UUID FK unique | 1:1 with intake |
| `review_status` | enum | See proposed enums |
| `reviewer` | string nullable | GitHub handle or user id string |
| `reviewer_user_id` | UUID FK nullable | If linked to backend User |
| `reviewed_at` | timestamptz nullable | |
| `decline_reason_code` | enum nullable | Required when declined |
| `duplicate_of` | string nullable | Intake id, Sheet row, or URL |
| `notes_internal` | text nullable | Never public |
| `pii_redacted` | boolean | Default false |
| `import_ready` | boolean | Default false; server-gated |
| `escalation_level` | enum | Default `none` |
| `created_at`, `updated_at` | timestamps | |

**Indexes (proposed):** `review_status`, `import_ready`, `escalation_level`, composite queue index.

### ModerationAuditEvent (or audit_logs extension)

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | |
| `intake_submission_id` | UUID FK | |
| `actor_user_id` | UUID FK nullable | |
| `action` | string | e.g. `intake.review_status_changed` |
| `old_value` | jsonb nullable | |
| `new_value` | jsonb nullable | |
| `metadata` | jsonb | |
| `created_at` | timestamptz | Append-only |

Existing `audit_logs` may suffice if `entity_type` + `metadata_json` cover intake events.

### Report (unchanged role)

- Remains tied to `job_posting_id` for in-app community reports.
- `verified` / `dismissed` / `disputed` remain backend reporting states.
- **`approved_for_import` does not map to `verified`.**
- Optional future FK: `intake_submission_id` on Report for imported rows (traceability).

## Proposed Enums

**PROPOSED — names require maintainer approval.**

### review_status (intake moderation)

| Value | Notes |
| ----- | ----- |
| `new` | Unreviewed (Sheet default) |
| `reviewing` | Alias for SOP `in_review` |
| `approved_for_import` | Import-eligible |
| `declined` | Generic declined; use with `decline_reason_code` |
| `duplicate` | Terminal duplicate |
| `needs_more_info` | Proposed; not in SOP today |
| `escalated` | Blocked until resolved |

Map SOP granular `declined_*` values to `declined` + specific `decline_reason_code` in API layer.

### decline_reason_code

Align with SOP: `duplicate`, `spam`, `insufficient_evidence`, `not_ghost_job`, `pii`, `invalid_url`, `no_consent`, `other`.

Wireframe proposed additional codes (`unsafe_content`, `out_of_scope`) — **maintainer decision** whether to extend SOP or map to `other`.

### escalation_level

SOP today: `none`, `maintainer`, `lead`. Wireframe used low/medium/high — **recommend retaining SOP values** for schema/API parity.

### source

`google_form_sheet`, `manual_admin`, `future_api`

## State Mapping

| Sheet / intake moderation state | Backend ReportStatus | Import readiness | Public visibility | Notes |
| --------------------------------- | -------------------- | ---------------- | ----------------- | ----- |
| `new` | N/A | No row | None | No intake record until imported |
| `reviewing` / `in_review` | N/A | Not import-ready | None | |
| `approved_for_import` | N/A (pre-import) | Eligible after checklist | None | Not `verified` |
| `approved_for_import` + import | `pending` (planned) | Post-import row | Internal until verified | [sheet-import-design.md](sheet-import-design.md) |
| `declined_*` | N/A | No import | None | |
| `duplicate` | N/A | No import | None | |
| `needs_more_info` | N/A | No import | None | Proposed |
| `escalated` | N/A | Blocked | None | |
| `pending` (Report) | `pending` | N/A if in-app only | Restricted | In-app report |
| `verified` | `verified` | Separate from import approval | Scoring impact | Community/employer visible per product rules |
| `dismissed` | `dismissed` | Terminal | Hidden | |
| `disputed` | `disputed` | N/A | Restricted | Employer-driven |

**No one-to-one mapping** between Sheet `approved_for_import` and Report `verified`.

## Import Readiness Rules

Proposed server-side validation (future; mirrors [sheet_import.py](../backend/app/services/sheet_import.py)):

1. `import_ready = true` only when `review_status = approved_for_import`.
2. `pii_redacted = true` required.
3. `consent = true` required.
4. `duplicate_of` empty unless `review_status = duplicate`.
5. `decline_reason_code` required when `review_status` is declined/duplicate.
6. `escalation_level` must be `none` or resolved before import_ready.
7. `notes_internal` never exposed in public API responses.
8. `optional_contact_email` masked by default in API; reveal audited separately.
9. UI and API must not trigger `--apply`.
10. Production import remains blocked until Live Gates and maintainer approval.

## Migration Considerations

- **No migration in Batch 14D.**
- Future migration requires separate Batch 14G plan and maintainer approval.
- Existing `reports` data must remain compatible; additive tables preferred.
- Nullable columns only if extending existing tables (not recommended for Report).
- Queue indexes: `(review_status, submitted_at)`, `(import_ready)`, partial indexes for open queue.
- Unique constraint: `(source, source_external_id)` for Sheet idempotency.
- `duplicate_of` FK: polymorphic string (intake UUID vs Sheet row vs URL) — document reference type enum.
- Audit retention policy TBD before production.
- Rollback: drop new tables without touching `reports` if import not yet run.
- Test path: local Docker Alembic upgrade/downgrade; staging before production.

## API Impact

| Area | Future need |
| ---- | ----------- |
| GET intake queue | New endpoint; filters on ModerationReview fields |
| GET intake detail | Extended DTO with intake + review + masked email |
| PATCH review | Validates state machine + import gates |
| POST duplicate | Sets duplicate_of + status |
| GET audit | List events for intake id |
| PII reveal | Optional audited endpoint |
| Existing verify/dismiss | Unchanged for in-app Report until deprecation decision |

Do not overload POST verify/dismiss with Sheet SOP semantics without explicit API version decision.

## UI Impact

| Screen | Schema dependency |
| ------ | ----------------- |
| Queue | ModerationReview + IntakeSubmission join; filters on review_status, import_ready, escalation |
| Detail | Full intake fields; moderation metadata section |
| PII panel | `pii_redacted`, masked `optional_contact_email` |
| Duplicate panel | `duplicate_of`, search on normalized URL |
| Decision panel | Enum-driven validation |
| Audit/history | ModerationAuditEvent or audit_logs by entity |
| Admin settings | Enum reference data |
| Responsive/a11y | Status labels from enum display names, not raw DB values |

## Privacy and Security Impact

| Topic | Decision direction |
| ----- | ------------------ |
| Optional contact email | Store on IntakeSubmission only; API masked; encryption at rest TBD |
| Internal notes | `notes_internal` never in public DTOs |
| Audit metadata | May contain redaction summaries; no raw PII in logs |
| RBAC | Required before hosted exposure; beyond `is_admin` |
| Sheet bridge | No raw row dumps in API responses |
| Secrets | Never in audit metadata or client logs |
| CORS | Approved before hosted frontend |
| Rate limiting | On moderation write endpoints when public |

## Testing Requirements

Future test coverage:

| Category | Tests |
| -------- | ----- |
| Migration | Upgrade/downgrade; table existence; indexes |
| Models | Validation constraints; enum values |
| Import gates | import_ready, consent, pii, duplicate, escalation |
| Decline | reason required |
| Duplicate | duplicate_of required |
| Audit | Event on status change, email reveal |
| Email masking | Absent from list/detail default |
| API auth | Admin/moderator RBAC |
| Backward compat | Existing moderation endpoints unchanged |
| No apply | No code path sets imported_report_id without approved `--apply` batch |
| Dry-run parity | Intake eligibility matches sheet_import rules |

## Decision

**Planning decision (Batch 14D):** Future implementation should introduce a separate **IntakeSubmission** domain for Google Form / Sheet intake and a **ModerationReview** layer (separate table preferred over embedded columns for audit clarity). **Report** and **ReportStatus** remain the in-app public/reporting lifecycle. Do not expand `ReportStatus` to carry Sheet import workflow state.

This decision is **docs-only**. Implementation requires Batch 14E (API plan), 14G (migration plan), and explicit maintainer approval before any Alembic revision or model code.

## Consequences

1. Clear separation of intake staging vs public report lifecycle.
2. More migration and API surface than adding columns to Report.
3. Better auditability and privacy boundaries for contact email and notes.
4. Reduced risk of treating `verified` reports as import-approved Sheet rows.
5. In-app moderation endpoints remain valid during transition.
6. Sheet bridge and UI work target IntakeSubmission, not Report queue alone.
7. Batch 14E/F/G must reference this record before implementation.

## Open Questions

1. **One vs two tables:** ModerationReview separate, or embed moderation columns on IntakeSubmission?
2. **Contact email:** Encrypt at rest, tokenize, or omit from DB and keep Sheet-only until policy set?
3. **External ID:** Sheet row number vs Form response timestamp vs content hash for idempotency?
4. **Enum exactness:** Mirror all SOP `declined_*` statuses vs single `declined` + code?
5. **duplicate_of type:** UUID FK to intake, string row id, or normalized URL — polymorphic reference?
6. **needs_more_info:** Add to SOP and schema, or defer?
7. **Audit retention:** Retention period and export policy?
8. **RBAC roles:** moderator, admin, auditor — map to backend User flags?
9. **First deploy target:** Local Docker only vs Render staging?
10. **Backfill:** Import historical Sheet rows into IntakeSubmission or forward-only?

## Non-Implementation Boundary

- No code changed in Batch 14D
- No database migration or Alembic revision
- No API or UI implementation
- No deploy or cloud resources
- No live Sheet gate change
- No `--apply` implementation or execution

## Recommended Next Batches

| Batch | Scope | Type |
| ----- | ----- | ---- |
| **14E** | Moderation API implementation plan (endpoint rollout order) | Docs-only |
| **14F** | Moderation frontend implementation plan | Docs-only |
| **14G** | Moderation migration plan (Alembic strategy, rollback) | Docs-only |
| **14A** | Render staging implementation | Deploy — explicit infra approval |

**Next recommended batch:** **14E** — moderation API implementation plan (docs-only).

## Related Documents

- [moderation-ui-scope.md](moderation-ui-scope.md)
- [moderation-api-contract-review.md](moderation-api-contract-review.md)
- [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md)
- [sheet-import-design.md](sheet-import-design.md)
- [sheet-import-apply-design.md](sheet-import-apply-design.md)
- [moderation-sop.md](moderation-sop.md)
