# Moderation API Implementation Plan

## Status

Batch 14E docs-only. No API implementation. No backend source changes. No schema changes. No migrations. No deploy performed.

Baseline commit: `b8e2ee2` (main CI and Pages green before this batch).

## Source Documents

| Document | Batch | Purpose |
| -------- | ----- | ------- |
| [moderation-ui-scope.md](moderation-ui-scope.md) | 13E | UI capabilities and non-goals |
| [moderation-api-contract-review.md](moderation-api-contract-review.md) | 14B | Existing vs proposed API contract |
| [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md) | 14C | Screen flows and API dependencies |
| [moderation-schema-decision-record.md](moderation-schema-decision-record.md) | 14D | IntakeSubmission + ModerationReview direction |
| [sheet-import-design.md](sheet-import-design.md) | 10D | Field mapping and import lifecycle |
| [sheet-import-apply-design.md](sheet-import-apply-design.md) | 12B | Apply-mode gates (`--apply` blocked) |

## Current Baseline

| Layer | State |
| ----- | ----- |
| Public MVP intake | GitHub Pages + Google Form + manual Sheet moderation |
| Backend hosting | Local Docker only |
| Current moderation API | Three admin endpoints on in-app `Report` records |
| `ReportStatus` | `pending`, `verified`, `dismissed`, `disputed` |
| Sheet SOP moderation | Richer; separate from backend `ReportStatus` |
| Schema direction (14D) | **IntakeSubmission** + **ModerationReview**; `Report` unchanged |
| Offline Sheet Gates 11/12 | **ACCEPTED-MVP** (Section 18 amendment) |
| Live Sheet Gates 11/12 | **BLOCKED-LIVE** |
| `--apply` / production import | **Blocked** |

Form/Sheet intake does not create backend rows today. Existing moderation APIs serve in-app reports submitted via `POST /api/v1/reports` against existing job postings.

## Implementation Goal

Define a future admin-only moderation API that:

1. Exposes intake submission queue and detail for the future moderation UI (Batch 14C).
2. Keeps `Report` lifecycle separate from intake/import lifecycle (Batch 14D).
3. Enforces Sheet SOP validation and import readiness server-side, aligned with [sheet_import.py](../backend/app/services/sheet_import.py).
4. Provides durable audit events for every state-changing action.
5. Protects optional contact email and internal notes at the API layer.
6. Prevents any UI or API path from triggering `--apply` or production import.

## Non-Goals

- No implementation in Batch 14E
- No schema migration in Batch 14E
- No frontend UI implementation
- No production import automation
- No `--apply` trigger from any endpoint
- No public anonymous moderation access
- No hosted deployment authorization
- No live Sheet gate status change
- No Google Sheets API bridge in initial API phases (deferred)

## Existing API Baseline

All routes mounted under `/api/v1/moderation` ([backend/app/api/v1/moderation.py](../backend/app/api/v1/moderation.py)). Service: [backend/app/services/moderation.py](../backend/app/services/moderation.py).

### GET /api/v1/moderation/reports

| Aspect | Detail |
| ------ | ------ |
| Model target | `Report` |
| Auth | Bearer JWT; `require_admin` (`is_admin = true`) |
| Query params | `status` (default `pending`); `page` (default 1); `page_size` (default 20, max 100) |
| State transition | None (read-only) |
| Audit | None |
| Response | `ReportListResponse`: `items[]`, `total`, `page`, `page_size`; items are `ReportResponse` |
| Ordering | Oldest first (`created_at asc`) |
| Limitations | No Sheet SOP fields; no intake queue; no search/filter beyond status |

### POST /api/v1/moderation/reports/{report_id}/verify

| Aspect | Detail |
| ------ | ------ |
| Model target | `Report` |
| Auth | Admin JWT |
| State transition | `pending` or `disputed` → `verified` |
| Side effects | Score recalculation; score snapshots |
| Audit | `report.verified` via [audit.py](../backend/app/services/audit.py); metadata: `job_posting_id`, `previous_status`, `new_status` |
| Limitations | Not equivalent to Sheet `approved_for_import`; no intake workflow |

### POST /api/v1/moderation/reports/{report_id}/dismiss

| Aspect | Detail |
| ------ | ------ |
| Model target | `Report` |
| Auth | Admin JWT |
| Request body | Optional `DismissReportRequest`: `{ "reason": "..." }` (max 2000 chars); stored in audit metadata only |
| State transition | `pending` or `disputed` → `dismissed` (terminal) |
| Side effects | Score recalculation; score snapshots |
| Audit | `report.dismissed` with optional `reason` in metadata |
| Limitations | No structured `decline_reason_code`; not Sheet `declined_*` semantics |

### Clarifications

- These endpoints operate on **Report** only.
- They do **not** implement Sheet SOP `review_status`.
- They must **not** be overloaded with import workflow state without explicit maintainer approval.
- No `GET /api/v1/moderation/reports/{id}` exists today.
- No GET audit API exists today.

Tests: [backend/tests/test_moderation.py](../backend/tests/test_moderation.py) — admin ACL, list, verify, dismiss, audit creation, score snapshots, invalid transitions.

## Required Schema Prerequisites

API implementation depends on a later schema/migration plan (Batch 14G). Per [moderation-schema-decision-record.md](moderation-schema-decision-record.md):

| Entity | Role |
| ------ | ---- |
| `IntakeSubmission` | Form/Sheet intake staging record |
| `ModerationReview` | 1:1 SOP moderation state linked to intake |
| `ModerationAuditEvent` or extended `audit_logs` | Append-only moderation history |

**Gate:** API implementation must not begin until:

1. Schema decision (14D) is accepted by maintainer.
2. Migration plan (14G) is approved and Alembic revision exists.
3. Local Docker migration upgrade/downgrade tests pass.

Report model and existing moderation endpoints remain unchanged during intake API rollout.

## Proposed API Surface

**All endpoints below are PROPOSED — NOT IMPLEMENTED.** Route names require maintainer approval. Sheet bridge endpoints remain deferred unless separately approved.

Router prefix proposal: `/api/v1/intake-submissions` (separate from `/api/v1/moderation/reports`).

---

### GET /api/v1/intake-submissions

**Purpose:** List intake submissions for the moderation queue.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT (initial); future moderator role |
| Query params | `review_status` (multi-value); `import_ready` (bool); `pii_redacted` (bool); `escalation_level`; `source`; `submitted_after`; `submitted_before`; `q` (company name or URL fragment); `page` (default 1); `page_size` (default 20, max 100); `sort` (`submitted_at`, `updated_at`; default `submitted_at desc`) |
| Response DTO | `IntakeSubmissionListResponse`: `items[]`, `total`, `page`, `page_size` |
| Summary item fields | `id`, `source`, `submitted_at`, `job_posting_url`, `company_name`, `job_title`, `review_status`, `import_ready`, `pii_redacted`, `escalation_level`, `reviewer`, `reviewed_at` |
| Privacy | `optional_contact_email` **excluded** from list; `notes_internal` **excluded** |
| Errors | `401`, `403` |
| Tests | Admin required; filter combinations; pagination bounds; masked email absent from list |

---

### GET /api/v1/intake-submissions/{id}

**Purpose:** Retrieve submission detail with moderation state.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT |
| Response DTO | `IntakeSubmissionDetailResponse`: intake fields + nested `ModerationReviewResponse` |
| Visible by default | All Form fields; moderation metadata; `optional_contact_email_masked` (e.g. `j***@example.com`) |
| Hidden by default | Raw `optional_contact_email`; full email requires separate reveal action (future) |
| Internal notes | `notes_internal` visible to admin/moderator only; never in public DTOs |
| Not found | `404` |
| Forbidden | `403` for non-admin |
| Tests | Detail shape; masked email; notes present for admin; 404 for unknown id |

---

### PATCH /api/v1/intake-submissions/{id}/review

**Purpose:** Update `review_status` and review metadata.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT |
| Request body | `UpdateModerationReviewRequest` (all fields optional except when required by target state): `review_status`, `reviewer`, `decline_reason_code`, `duplicate_of`, `notes_internal`, `pii_redacted`, `import_ready`, `escalation_level`, `expected_updated_at` (optimistic concurrency) |
| Validation | State machine (see State Transitions); field rules (see Validation Rules); server recomputes `import_ready` when requested |
| Audit | `review.status_changed` (+ field-specific events) on every successful update |
| Stale update | `409` when `expected_updated_at` does not match current row |
| Response | Updated `IntakeSubmissionDetailResponse` |
| Errors | `400`, `401`, `403`, `404`, `409`, `422` |
| Tests | Valid transitions; invalid transitions; required fields per state; audit event created; stale conflict |

---

### POST /api/v1/intake-submissions/{id}/pii-redaction

**Purpose:** Record PII redaction review completion.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT |
| Request body | `{ "pii_redacted": true, "notes_internal": "..." }` (notes optional) |
| Validation | Cannot set `pii_redacted=true` if contact email or narrative still contains unreviewed PII markers (future content scan optional; manual attestation in v1) |
| Audit | `pii.redaction_changed` |
| Response | Updated moderation review section |
| Tests | Audit event; gate interaction with import readiness |

---

### POST /api/v1/intake-submissions/{id}/duplicate

**Purpose:** Mark submission as duplicate and set `duplicate_of`.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT |
| Request body | `{ "duplicate_of": "<uuid|url|sheet_row>", "duplicate_target_type": "intake_submission|url|sheet_row", "notes_internal": "..." }` |
| Validation | `duplicate_of` required; sets `review_status=duplicate`; clears `import_ready`; sets `decline_reason_code=duplicate` |
| Audit | `duplicate.set` |
| Response | Updated detail DTO |
| Tests | Required duplicate_of; import_ready cleared; audit event |

---

### GET /api/v1/intake-submissions/{id}/audit

**Purpose:** Retrieve moderation audit/history events.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT; future auditor read-only role |
| Query params | `page`, `page_size` (default 20, max 100) |
| Response | `ModerationAuditEventListResponse`: `items[]`, `total`, `page`, `page_size` |
| Event fields | `id`, `action`, `actor_user_id`, `actor_display`, `old_value`, `new_value`, `metadata`, `created_at` |
| Redaction | No raw contact email in metadata; redact PII from `notes_internal` snapshots if stored |
| Tests | Events returned in chronological order; pagination; auth required |

---

### GET /api/v1/intake-submissions/duplicates/search

**Purpose:** Search possible duplicate submissions by normalized job URL or company/title match.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT |
| Query params | `job_posting_url` (required); `exclude_id` (optional); `limit` (default 10, max 50) |
| Response | `DuplicateSearchResponse`: `matches[]` with `id`, `submitted_at`, `company_name`, `job_title`, `job_posting_url`, `review_status`, `match_confidence` (`exact_url`, `normalized_url`, `company_title`) |
| Privacy | No contact email in search results; no internal notes |
| Tests | URL normalization parity with [job_url_validation.py](../backend/app/services/job_url_validation.py); exclude self |

---

### POST /api/v1/intake-submissions/{id}/import-readiness

**Purpose:** Validate import readiness without importing or writing import records.

| Aspect | Detail |
| ------ | ------ |
| Auth | Admin JWT |
| Request body | None (reads current intake + review state) |
| Behavior | **Validation-only** — no DB import writes; no `--apply`; no `imported_report_id` mutation |
| Response | `ImportReadinessResponse`: `ready` (bool), `checks[]` each with `code`, `passed`, `message` |
| Check parity | Mirrors `check_eligibility` in [sheet_import.py](../backend/app/services/sheet_import.py): `review_status`, `import_ready`, `pii_redacted`, `decline_reason_code`, `duplicate_of`, `escalation_level`, `consent`, required fields, URL scheme |
| Tests | Pass/fail reason lists; no side effects on Report; no apply code path reachable |

---

### Deferred endpoints (not in initial rollout)

| Endpoint | Notes |
| -------- | ----- |
| POST `/api/v1/intake-submissions/{id}/contact-email/reveal` | Audited email reveal; requires elevated permission |
| POST `/api/v1/intake-submissions/import` | Actual import — blocked until `--apply` approved |
| Google Sheet sync read/write | Separate security review; not in Phase C–F |

## DTO and Field Design

**PROPOSED — NOT IMPLEMENTED.**

### IntakeSubmissionSummaryResponse

| Field | Type | Privacy |
| ----- | ---- | ------- |
| `id` | UUID | Public to admin |
| `source` | enum | Public to admin |
| `submitted_at` | datetime | Public to admin |
| `job_posting_url` | string | Public to admin |
| `company_name` | string | Public to admin |
| `job_title` | string | Public to admin |
| `review_status` | enum | Public to admin |
| `import_ready` | bool | Public to admin |
| `pii_redacted` | bool | Public to admin |
| `escalation_level` | enum | Public to admin |
| `reviewer` | string nullable | Public to admin |
| `reviewed_at` | datetime nullable | Public to admin |

### IntakeSubmissionDetailResponse

Extends summary with:

| Field | Type | Privacy |
| ----- | ---- | ------- |
| `location_or_remote` | string | Admin |
| `date_seen` | date | Admin |
| `suspicion_reason` | string | Admin |
| `company_response` | string | Admin |
| `consent` | bool | Admin |
| `evidence_links` | string nullable | Admin; render as safe links only |
| `optional_contact_email_masked` | string nullable | Admin; masked default |
| `optional_contact_email_reveal_allowed` | bool | Admin; permission hint |
| `source_external_id` | string nullable | Admin |
| `created_at`, `updated_at` | datetime | Admin |
| `moderation_review` | ModerationReviewResponse | Admin |
| `imported_report_id` | UUID nullable | Admin; read-only |

### ModerationReviewResponse

| Field | Type | Privacy |
| ----- | ---- | ------- |
| `review_status` | enum | Admin |
| `reviewer` | string nullable | Admin |
| `reviewer_user_id` | UUID nullable | Admin |
| `reviewed_at` | datetime nullable | Admin |
| `decline_reason_code` | enum nullable | Admin |
| `duplicate_of` | string nullable | Admin |
| `notes_internal` | string nullable | Admin only; never public |
| `pii_redacted` | bool | Admin |
| `import_ready` | bool | Admin; server-gated |
| `escalation_level` | enum | Admin |

### ModerationAuditEventResponse

| Field | Type | Privacy |
| ----- | ---- | ------- |
| `id` | UUID | Admin/auditor |
| `action` | string | Admin/auditor |
| `actor_user_id` | UUID nullable | Admin/auditor |
| `actor_display` | string | Admin/auditor |
| `old_value` | object nullable | Redacted |
| `new_value` | object nullable | Redacted |
| `metadata` | object | Redacted |
| `created_at` | datetime | Admin/auditor |

### ValidationErrorResponse

Follow existing FastAPI pattern: `{ "detail": "<message>" }` via [exceptions.py](../backend/app/exceptions.py). For multi-field validation, use structured detail list consistent with Pydantic v2 error format when batch validation is added.

## Validation Rules

Server-side rules (future implementation):

| Rule | Enforcement |
| ---- | ----------- |
| Valid consent | `consent=true` required before `review_status=approved_for_import` |
| PII redaction | `pii_redacted=true` required before `import_ready=true` |
| Import ready gate | `import_ready=true` only when `review_status=approved_for_import` and all checklist checks pass |
| Decline reason | `decline_reason_code` required when `review_status=declined` or `duplicate` |
| Duplicate reference | `duplicate_of` required when `review_status=duplicate`; forbidden otherwise |
| Escalation | `escalation_level` must be `none` (or resolved) before `import_ready=true` |
| Internal notes | `notes_internal` never returned in public or unauthenticated responses |
| Contact email | Masked in all default responses; reveal requires audited separate action |
| URL scheme | `job_posting_url` must pass `validate_http_https_url` ([job_url_validation.py](../backend/app/services/job_url_validation.py)) |
| Stale update | `expected_updated_at` mismatch returns `409 ConflictError` |
| No apply path | No endpoint sets `imported_report_id` or invokes sheet import apply logic |
| Field length | Align with Form constraints and existing schema max lengths |

Server should recompute `import_ready` rather than trusting client-only toggles when transitioning to `approved_for_import`.

## State Transitions

**Sheet `review_status` is not `ReportStatus`.** `approved_for_import` is not equivalent to `verified`. `dismissed` (Report) is not equivalent to `declined` (intake) without explicit mapping.

| Current state | Allowed next states | Required fields | Blocked | Audit event | Import implication |
| ------------- | ------------------- | --------------- | ------- | ----------- | ------------------ |
| `new` | `reviewing`, `declined`, `duplicate`, `escalated` | — | `approved_for_import` | `review.status_changed` | Not import-ready |
| `reviewing` | `approved_for_import`, `declined`, `duplicate`, `needs_more_info`, `escalated` | — | Direct `import_ready` without approval | `review.status_changed` | Not import-ready |
| `approved_for_import` | `reviewing`, `declined`, `escalated` | consent valid; checklist pass for `import_ready` | `import_ready` if gates fail | `review.status_changed`, `import_ready.changed` | Eligible when gates pass |
| `declined` | `reviewing` (reopen) | `decline_reason_code` | `import_ready=true` | `review.status_changed`, `decline.reason_set` | No import |
| `duplicate` | — (terminal) | `duplicate_of`, `decline_reason_code=duplicate` | All import paths | `duplicate.set` | No import |
| `needs_more_info` | `reviewing`, `declined` | — | `approved_for_import` until resolved | `review.status_changed` | No import |
| `escalated` | `reviewing`, `declined` | escalation note recommended | `import_ready=true` until resolved | `escalation.changed` | Blocked |

SOP granular `declined_*` values map to `declined` + specific `decline_reason_code` at the API layer.

## Auth and Authorization Plan

| Phase | Access model |
| ----- | ------------ |
| Initial (Phase C–F) | `require_admin` only — same as existing Report moderation |
| Future | `moderator` role: queue, detail, review write, PII redaction, duplicate |
| Future | `auditor` role: read-only queue, detail, audit history |
| Future | `email_reveal` permission: separate from base moderator |

Implementation details:

- JWT bearer auth via existing `get_current_user` dependency.
- RBAC beyond `is_admin` required before hosted frontend exposure.
- CORS allowlist approval required before hosted moderation UI calls API.
- Rate limiting on write endpoints before public network exposure (pattern exists for auth endpoints in [rate_limit.py](../backend/app/services/rate_limit.py)).

## Audit Plan

Prefer extending existing `audit_logs` with `entity_type=intake_submission` unless query patterns require a dedicated `moderation_audit_events` table (open question).

| Property | Detail |
| -------- | ------ |
| Mutability | Append-only; no update/delete |
| Actor | `actor_user_id` from JWT user |
| Timestamp | `created_at` on insert |
| Old/new values | JSON snapshots of changed moderation fields |
| Metadata redaction | Strip raw email; truncate long notes in snapshots if needed |
| Retention | Open question — see Open Questions |

### Event types

| Action | Trigger |
| ------ | ------- |
| `intake.created` | IntakeSubmission insert (import bridge or manual admin) |
| `review.started` | Transition to `reviewing` |
| `review.status_changed` | Any `review_status` change |
| `pii.redaction_changed` | PII redaction endpoint or review patch |
| `duplicate.set` | Duplicate marking |
| `decline.reason_set` | Decline reason assigned or changed |
| `import_ready.changed` | `import_ready` toggle or server recompute |
| `escalation.changed` | Escalation level change |
| `note.added` | Internal note append (if notes are append-only) |
| `contact_email.revealed` | Future reveal action |
| `validation.run` | Import readiness validation endpoint invoked |

Every state-changing endpoint must create at least one audit event in the same transaction.

## Import Readiness Plan

The `POST .../import-readiness` endpoint is **validation-only**:

1. Load intake + moderation review from DB.
2. Run checks equivalent to `check_eligibility` in [sheet_import.py](../backend/app/services/sheet_import.py).
3. Return structured pass/fail list.
4. **No** writes to `reports`, `job_postings`, or `imported_report_id`.
5. **No** invocation of `--apply` or apply-mode CLI.
6. UI may call this before showing "ready for future import" badge; badge must not imply apply is available.

Dry-run CLI remains the offline verification path until API parity is tested and `--apply` is separately approved.

## Error Handling Plan

Uses existing exception types from [exceptions.py](../backend/app/exceptions.py):

| HTTP | Exception | When |
| ---- | --------- | ---- |
| 400 | `ValidationError` or dedicated bad request | Malformed query/body |
| 401 | `UnauthorizedError` | Missing or invalid JWT |
| 403 | `ForbiddenError` | Authenticated non-admin |
| 404 | `NotFoundError` | Unknown intake id |
| 409 | `ConflictError` | Stale `expected_updated_at`; duplicate external id |
| 422 | `ValidationError` | Invalid state transition; missing required field |
| 429 | `RateLimitError` | Rate limit exceeded (when enabled) |
| 500 | Unhandled | Logged and re-raised; no silent swallow |

Response shape: `{ "detail": "<string or structured list>" }` consistent with current FastAPI handlers.

## Testing Plan

Future test modules (proposed: `backend/tests/test_intake_moderation.py`):

| Category | Tests |
| -------- | ----- |
| Auth | 401 without token; 403 non-admin |
| Queue list | Pagination; filters; sort; no masked email leakage |
| Detail | Field presence; masked email; notes visible to admin |
| Review PATCH | Valid/invalid transitions; required fields; 409 stale |
| Decline | `decline_reason_code` required |
| Duplicate | `duplicate_of` required; clears import_ready |
| PII / import_ready | Gate combinations; server recompute |
| Audit | Event on each write; GET audit pagination |
| Import readiness | Parity with sheet_import checks; no DB side effects |
| No apply | No code path creates Report or sets imported_report_id |
| Duplicate search | URL normalization; exclude_id |
| URL safety | Reject non-http(s) URLs |
| Backward compat | Existing [test_moderation.py](../backend/tests/test_moderation.py) unchanged and passing |
| Migration | Model fixtures require migrated schema (integration) |

## Migration and Rollout Plan

### Phase A: Schema migration plan (Batch 14G)

Docs-only Alembic strategy, rollback, indexes, enum definitions. **Prerequisite for all code phases.**

### Phase B: Add models and migrations (future code batch)

Create `IntakeSubmission`, `ModerationReview`, audit extension. Local Docker migration tests. **Maintainer approval required.**

### Phase C: Read-only intake queue/detail APIs (future code batch)

Implement GET list and GET detail only. Seed test fixtures. No write endpoints.

### Phase D: Moderation write APIs (future code batch)

PATCH review, POST pii-redaction, POST duplicate. State machine + validation + audit in same transaction.

### Phase E: Audit retrieval (future code batch)

GET audit history endpoint. Redaction rules applied.

### Phase F: Import-readiness validation endpoint (future code batch)

POST import-readiness. Parity tests against sheet_import logic.

### Phase G: Wire frontend UI (Batch 14F implementation, after API tests pass)

Frontend consumes Phase C–F endpoints. Local Docker E2E only initially.

### Phase H: Staging deployment (Batch 14A or later)

Render staging with explicit infra approval. CORS, RBAC, rate limiting enabled before exposure.

## Backward Compatibility

| Area | Requirement |
| ---- | ----------- |
| Report moderation endpoints | Unchanged; all existing tests pass |
| ReportStatus enum | No new values for import workflow |
| Public MVP static site | Unchanged |
| Sheet import dry-run CLI | Remains separate offline tool |
| `--apply` | Blocked until separate maintainer decision |
| Live Sheet gates | Remain **BLOCKED-LIVE** |

New intake routes are additive under a new router prefix; no breaking changes to `/api/v1/moderation/reports`.

## Security and Privacy Requirements

| Requirement | Detail |
| ----------- | ------ |
| No public moderation API | All intake endpoints require auth |
| Contact email | Masked by default; reveal audited |
| Internal notes | Never in public responses |
| No raw Sheet dumps | API returns structured DTOs only |
| No secrets in logs | Exclude email, tokens from log metadata |
| CORS | Allowlist before hosted frontend |
| Rate limiting | Write endpoints before network exposure |
| Safe URL rendering | Validate http/https; no javascript: URLs |
| Audit metadata | Redact PII from stored snapshots |
| RBAC | Required before staging/production moderation UI |

## Open Questions

1. Final route prefix: `/intake-submissions` vs `/moderation/intake-submissions`?
2. Exact enum values — mirror SOP or normalized subset?
3. One table vs two tables for intake + moderation review?
4. Extend `audit_logs` vs new `ModerationAuditEvent` table?
5. Optional contact email: encrypt at rest, tokenize, or omit from DB?
6. Exact RBAC role names and permission matrix?
7. `duplicate_of` target type: UUID FK, string, or polymorphic reference?
8. `needs_more_info`: add to SOP and whether it triggers reporter contact?
9. Sheet bridge timing: manual CSV ingest vs Google API?
10. First implementation target: local Docker only vs Render staging?
11. Audit retention period and export policy?
12. Append-only notes vs full replace on PATCH?

## Decision Boundaries

- Batch 14E is **planning-only**
- No code was changed
- No migration was created
- No API was implemented
- No UI was implemented
- No deploy occurred
- Live Gate 11/12 remain **BLOCKED-LIVE**
- `--apply` remains **blocked**

## Recommended Next Batches

| Batch | Scope | Type |
| ----- | ----- | ---- |
| **14F** | Moderation frontend implementation plan | Docs-only |
| **14G** | Moderation migration plan (Alembic strategy) | Docs-only |
| **14H** | Moderation API test plan (detailed test matrix) | Docs-only |
| **14A** | Render staging implementation | Deploy — explicit infra approval |

**Next recommended batch:** **14F** — moderation frontend implementation plan (docs-only).

## Related Documents

- [moderation-api-contract-review.md](moderation-api-contract-review.md)
- [moderation-schema-decision-record.md](moderation-schema-decision-record.md)
- [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md)
- [moderation-ui-scope.md](moderation-ui-scope.md)
- [moderation-api.md](moderation-api.md)
