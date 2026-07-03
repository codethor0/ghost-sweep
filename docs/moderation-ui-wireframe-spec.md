# Moderation UI Wireframe Spec

## Status

Batch 14C docs-only. No UI implemented. No backend changes. No deploy performed.

Baseline commit: `a74603c` (main CI and Pages green before this batch).

## Source Documents

| Document | Role |
| -------- | ---- |
| [moderation-ui-scope.md](moderation-ui-scope.md) | Batch 13E product scope, screens, workflow |
| [moderation-api-contract-review.md](moderation-api-contract-review.md) | Batch 14B existing vs proposed API contract |
| [sheet-import-design.md](sheet-import-design.md) | Import field mapping and eligibility |
| [sheet-import-apply-design.md](sheet-import-apply-design.md) | `--apply` gates (blocked) |
| [moderation-sop.md](moderation-sop.md) | Sheet review states and decline codes |

## Current Baseline

| Layer | State |
| ----- | ----- |
| Public MVP intake | GitHub Pages + Google Form + manual Sheet moderation |
| Backend hosting | Local Docker only |
| Existing moderation API | Three admin endpoints on in-app `Report` records only |
| Sheet SOP state model | Not represented on backend `Report` model |
| Frontend moderation UI | Not implemented; dashboard shows deferred notice |
| Production import / `--apply` | **Blocked** |
| Live Sheet Gates 11/12 | **BLOCKED-LIVE** |

Existing frontend patterns ([DashboardPanel.tsx](../frontend/components/dashboard/DashboardPanel.tsx)): Next.js App Router, in-memory JWT session, Tailwind CSS, `DeferredNotice` for unreleased features, admin flag displayed but no admin routes.

## Product Goal

The moderation UI wireframe spec defines a future admin surface that:

1. Reduces manual Sheet dependency over time.
2. Standardizes review decisions with enforced validation.
3. Protects optional contact email and other PII through masking and confirmation gates.
4. Supports human review before import readiness labeling.
5. Provides a path toward hosted backend moderation without bypassing review.
6. Keeps import execution (`--apply`, production automation) separate from moderation review.

## Non-Goals

- No UI implementation in Batch 14C
- No backend implementation or schema migration
- No production import or `--apply` trigger in UI
- No live Sheet gate change or reopening
- No automated publishing of moderated content
- No cloud deploy or Render resource creation
- No Google Form or Sheet changes
- No visual design system finalization (wireframe-level only)

## Users and Roles

| Role | Access today | Wireframe access |
| ---- | ------------ | ---------------- |
| Anonymous reporter | Form submit only | None |
| Moderator | Sheet Editor | Queue, detail, PII, duplicate, decision (future) |
| Maintainer / admin | Sheet Owner + `is_admin` | All screens + settings + escalation resolution |
| Read-only auditor | Not defined | Audit/history read-only (proposed) |
| Support reviewer | Not defined | Optional future: `needs_more_info` follow-up only |

**Current backend:** binary `is_admin` only ([require_admin](../backend/app/dependencies.py)). Role split (moderator vs admin vs auditor) is **proposed** and requires future RBAC. Auth provider is **TBD**.

## Information Architecture

```text
/login (or session gate)
  └── /moderation                    [admin/moderator]
        ├── /moderation/queue        default landing
        ├── /moderation/[id]         submission detail
        │     ├── #pii               PII review panel (section or tab)
        │     ├── #duplicates        duplicate review panel
        │     ├── #decision          decision panel
        │     └── #audit             audit/history
        ├── /moderation/settings     [admin only, future]
        └── /moderation/help         SOP reference (read-only)
```

| Nav item | Purpose | Roles |
| -------- | ------- | ----- |
| Login / access gate | Authenticate before moderation | All staff roles |
| Moderation queue | Triage and open submissions | Moderator, admin |
| Submission detail | Full review context | Moderator, admin |
| PII review | Redaction and confirmation | Moderator, admin |
| Duplicate review | Match and link duplicates | Moderator, admin |
| Decision panel | Apply review outcome | Moderator, admin |
| Audit / history | Accountability trail | Moderator, admin, auditor (read-only) |
| Admin / settings | Codes, thresholds, roles | Admin only |
| Help / SOP reference | Link to moderation-sop.md content | All staff roles |

**Route convention (proposed):** `/moderation/*` under existing Next.js app, separate from public `/dashboard`. Not implemented.

---

## Screen 1: Login or Access Gate

### Purpose

Authenticate staff before any moderation data is shown.

### Entry condition

User navigates to `/moderation` or any child route without valid admin session.

### Wireframe elements

| Element | Detail |
| ------- | ------ |
| Email/username field | Standard login form |
| Password field | Masked input |
| Submit button | "Sign in" |
| Error banner | Invalid credentials, rate limited |
| Session notice | Same as dashboard: in-memory token; refresh clears session (current behavior) |

### Empty state

N/A — form always shown when unauthenticated.

### Error states

| Condition | UI |
| --------- | -- |
| 401 invalid credentials | Inline error; no credential hint |
| 429 rate limited | "Too many attempts; try later" |
| Network failure | Retry prompt |

### Security constraints

- No moderation data rendered before auth succeeds.
- Non-admin authenticated users see **403 Forbidden** page, not queue.
- No secrets in client storage beyond short-lived access token (current pattern).

### Future API assumptions

- `POST /api/v1/auth/login` (existing)
- `GET /api/v1/auth/me` with `is_admin` check (existing)

### Status

**Not implemented.** Reuse existing `/login` with redirect to `/moderation` after admin check, or dedicated staff login (TBD).

---

## Screen 2: Moderation Queue

### Purpose

List submissions awaiting or in review; primary triage entry point.

### Table / list columns

| Column | Source today | Proposed |
| ------ | ------------ | -------- |
| `submitted_at` | Backend `created_at` (in-app) / Form Timestamp (Sheet) | Yes |
| Company | Job posting relation (partial) / Form column | Proposed join |
| Job title | Job posting (partial) / Form column | Proposed |
| Location or remote | Not on Report | Form / intake DTO |
| `review_status` or report status | Backend `status` only | Sheet `review_status` proposed |
| `pii_redacted` | Not on backend | Proposed |
| `import_ready` | Not on backend | Proposed |
| `escalation_level` | Not on backend | Proposed |
| Duplicate indicator | Not on backend | Derived from `duplicate_of` |
| Reviewer | Not on Report | Proposed |
| `reviewed_at` | `updated_at` proxy only | Proposed |

**Minimal viable queue (existing API):** `id`, `report_type`, `description` excerpt, `status`, `created_at`, `job_posting_id` from `GET /api/v1/moderation/reports`.

### Filters

| Filter | Values |
| ------ | ------ |
| Status | `new`, `in_review`, `approved_for_import`, `declined_*`, `escalated` (Sheet); `pending`, `verified`, `dismissed`, `disputed` (backend) |
| PII | `pii_redacted` yes/no/unknown |
| Import ready | yes/no |
| Escalation | none / maintainer / lead |
| Assigned reviewer | me / unassigned / all |
| Duplicate | has duplicate flag |

Backend today: filter by `status` query param only.

### Sorting

Default: oldest first (matches backend `created_at asc`). Optional: company, escalation priority.

### Search

Proposed: job URL fragment, company name, job title (requires API). Not available on current list endpoint.

### Batch actions

**Deferred in v1 wireframe.** No bulk approve/import. Single-item review only to reduce error risk.

### Empty states

| State | Message |
| ----- | ------- |
| No pending items | "No submissions awaiting review." |
| Filter no match | "No items match these filters." |

### Loading / error states

| State | UI |
| ----- | -- |
| Loading | Skeleton rows or spinner |
| 403 | Redirect to forbidden page |
| 401 | Redirect to login |
| 500 / network | Retry banner; preserve filter state |

### Privacy constraints

- Optional contact email **never** in queue columns.
- Description excerpt truncated; no full narrative in list.
- Internal notes never in list.

---

## Screen 3: Submission Detail

### Purpose

Full context for one submission with links to PII, duplicate, decision, and audit panels.

### Layout sections

```text
+--------------------------------------------------+
| Header: company / title / location               |
| Status badges: review_status, escalation, PII    |
+--------------------------------------------------+
| Job posting summary                              |
|   URL (link, scheme-validated)                   |
|   Normalized URL preview (proposed)                |
+--------------------------------------------------+
| Reporter-provided reason                         |
|   Narrative (full text)                          |
|   Date seen, company response (Form fields)        |
+--------------------------------------------------+
| Evidence links                                   |
|   List of http/https URLs; open in new tab         |
+--------------------------------------------------+
| Consent status                                   |
|   Checked / not checked — blocking badge if no   |
+--------------------------------------------------+
| Optional contact email                           |
|   [Masked]  [Reveal — requires confirmation]     |
+--------------------------------------------------+
| Internal moderation metadata                     |
|   reviewer, reviewed_at, decline_reason_code     |
|   duplicate_of, notes (internal)                 |
|   pii_redacted, import_ready, escalation_level     |
+--------------------------------------------------+
| Action bar                                       |
|   [PII Review] [Duplicates] [Decision] [Audit]   |
+--------------------------------------------------+
| Audit preview (last 3 events)                    |
+--------------------------------------------------+
```

### Data shown by default

Form fields, job URL, narrative, evidence links, consent, status badges, truncated audit preview.

### Data hidden by default

Optional contact email (masked), full internal notes if marked sensitive (proposed: always collapsed with expand).

### Action buttons

Navigate to panel sections; "Claim review" sets `in_review` + reviewer (proposed PATCH).

### Validation warnings

| Warning | Trigger |
| ------- | ------- |
| Consent not checked | Block approve/import_ready |
| Dangerous URL scheme | Block approve; suggest decline |
| Open escalation | Block import_ready |
| PII not confirmed | Block import_ready |

### Safe handling of optional contact email

Display: `j***@example.com` or "Contact email on file (hidden)". Reveal button opens confirmation modal: "Reveal contact email for follow-up only; action will be logged." Audit event on reveal (proposed).

### Future API

- `GET /api/v1/moderation/reports/{id}` — **proposed** (extended DTO)
- Today: compose from `GET /api/v1/reports/{id}` + job posting fetch (partial; not admin-gated)

---

## Screen 4: PII Review Panel

### Purpose

Guide moderator through PII check before approval or import readiness.

### Visible fields

Narrative, evidence link text, optional contact email (masked), reporter identity if present.

### Masked fields

Optional contact email by default. Third-party PII in narrative highlighted (proposed heuristic; manual review required).

### Redaction workflow

1. Moderator reviews narrative and links.
2. If PII found: redact in notes summary OR decline with `decline_reason_code=pii`.
3. Toggle `pii_redacted=yes` with checkbox: "I confirm PII has been reviewed and handled per SOP."
4. Cannot proceed to `import_ready=yes` until checkbox checked.

### `pii_redacted` state

| Value | UI |
| ----- | -- |
| unset / no | Warning badge; blocks import_ready |
| yes | Green indicator |

### Warnings

- "Optional contact email must not be published."
- "Decline if unrecoverable prohibited PII in narrative."

### Required confirmation

Modal before `pii_redacted=yes`: "Confirm PII review complete per SOP."

### Error states

Save failed; validation failed if attempting import_ready without PII confirmation.

### Privacy rules

- Notes are internal only; never on public surfaces.
- UI must not expose private notes in URLs, console, or client logs.

---

## Screen 5: Duplicate Review Panel

### Purpose

Surface likely duplicates and set `duplicate_of` when confirmed.

### Duplicate candidate list

| Column | Detail |
| ------ | ------ |
| Match confidence | High / medium / low (proposed) |
| Submitted at | Timestamp |
| Company + title + location | Comparison fields |
| Job URL | Normalized match |
| Current status | Prior review_status |
| Link | Open candidate detail |

### Comparison fields

Side-by-side or stacked: URL, company, title, location, narrative excerpt.

### `duplicate_of` behavior

On confirm duplicate: set `review_status=declined_duplicate`, `decline_reason_code=duplicate`, `duplicate_of` = row id or canonical URL. Terminal state.

### No-match behavior

"Mark as not duplicate" clears duplicate flag; returns to decision panel.

### Confidence label

Derived from normalized URL exact match (high) vs company+title+location (medium). Manual override always available with required note.

### Reviewer override

Override requires internal note explaining false positive.

### Future API

- `GET /api/v1/moderation/duplicates/search?url=...` — **proposed**
- No backend duplicate search today

---

## Screen 6: Decision Panel

### Purpose

Apply review outcome with enforced validation.

### Allowed decisions

| Decision | Maps to Sheet | Backend in-app (today) |
| -------- | --------------- | ---------------------- |
| `approved_for_import` | Yes | N/A (use verify separately for in-app) |
| `reviewing` / `in_review` | Yes | N/A |
| `declined_*` | Yes | dismiss + reason (partial) |
| `duplicate` | Yes | N/A |
| `needs_more_info` | Proposed | N/A |
| `escalated` | Yes | N/A |
| Verify (in-app) | N/A | POST verify |
| Dismiss (in-app) | N/A | POST dismiss |

### Required fields by decision

| Decision | Required fields |
| -------- | --------------- |
| `approved_for_import` | consent valid, `pii_redacted=yes`, narrative sufficient |
| `import_ready=yes` | all import checklist items (see rules) |
| `declined_*` | `decline_reason_code`, `notes` recommended |
| `duplicate` | `duplicate_of`, `decline_reason_code=duplicate` |
| `escalated` | `escalation_level`, `notes` |
| `needs_more_info` | `notes` (proposed) |
| Verify | none (backend) |
| Dismiss | optional reason (backend); proposed: decline code |

### Validation rules

1. `approved_for_import` requires valid consent.
2. `approved_for_import` requires `pii_redacted=yes`.
3. `import_ready=yes` requires `review_status=approved_for_import` and full checklist.
4. Declined requires `decline_reason_code`.
5. Duplicate requires `duplicate_of`.
6. `escalation_level` defaults to `none`.
7. Notes internal only.
8. **UI must not trigger `--apply` or any import execution.**

### Confirmation behavior

| Action | Confirmation |
| ------ | -------------- |
| Approve for import | "Confirm approval; this does not import to database." |
| Import ready yes | "Confirm import readiness label only; import remains manual/blocked." |
| Decline / duplicate | Single confirm with reason visible |
| Verify / dismiss (in-app) | Confirm for verify; dismiss shows reason preview |

### State transition summary

See [State and Validation Matrix](#state-and-validation-matrix) below.

---

## Screen 7: Audit and History

### Purpose

Show tamper-evident review trail for accountability.

### Audit events (proposed UI labels)

| Event | Source today |
| ----- | ------------ |
| Submission received | Form timestamp / report `created_at` |
| Reviewer assigned | Proposed |
| PII reviewed | Proposed |
| Decision changed | `report.verified`, `report.dismissed` in audit_logs |
| Duplicate set | Proposed |
| Import ready changed | Proposed |
| Note added | Proposed |
| Escalation changed | Proposed |
| Email revealed | Proposed |

### Fields per event

`timestamp`, `actor` (username or id), `action`, `summary`, `metadata` (collapsed JSON for admins).

### Visibility

Moderator and admin: full internal audit. Auditor: read-only, no email reveal metadata content (proposed).

### Tamper-resistance expectations

Append-only audit log in backend; UI read-only. Sheet history relies on SOP until bridged.

### Current backend gap

Audit writes exist for verify/dismiss; **no GET audit API**. UI would be empty or partial for in-app actions only.

### Future API

- `GET /api/v1/moderation/reports/{id}/audit` — **proposed**

---

## Screen 8: Admin or Settings

### Purpose

Reference configuration and role management (future).

### Role access

Admin only. Moderators see Help/SOP link instead.

### Configuration items (future-only)

| Setting | Purpose |
| ------- | ------- |
| Decline reason codes | Read-only list from SOP |
| Escalation levels | none / maintainer / lead |
| Reviewer roles | TBD RBAC |
| Duplicate thresholds | URL vs fuzzy match sensitivity |
| Email reveal permissions | Which roles may reveal |
| Frontend API base URL | Local vs staging |

### Status

**Not implemented.** Wireframe placeholder only.

---

## State and Validation Matrix

Backend `ReportStatus` and Sheet `review_status` are **not equivalent**.

| UI state | Source of truth | Required fields | Allowed actions | Blocked actions | Error if violated |
| -------- | --------------- | --------------- | --------------- | --------------- | ----------------- |
| `pending` (backend) | Report.status | — | Verify, dismiss, open detail | Verify if not pending/disputed | 422 invalid transition |
| `pending` (Sheet `new`) | Sheet row | — | Claim, decline, escalate | import_ready | import_ready rejected |
| `reviewing` / `in_review` | Sheet | reviewer, reviewed_at | PII, duplicate, decision | import_ready without PII | Validation message |
| `approved_for_import` | Sheet | consent, pii_redacted=yes | Set import_ready | import without checklist | Gate message |
| `declined_*` | Sheet | decline_reason_code | View only | Re-open (Sheet manual) | — |
| `duplicate` | Sheet | duplicate_of | View only | Approve | — |
| `needs_more_info` | Proposed | notes | Internal flag | import_ready | — |
| `escalated` | Sheet | escalation_level, notes | Resolve | import_ready | Open escalation block |
| `verified` (backend) | Report.status | — | Dismiss if disputed path | Re-verify without dispute | 422 |
| `dismissed` (backend) | Report.status | — | None | Re-open | 422 terminal |
| `disputed` (backend) | Report.status | — | Verify, dismiss | — | 422 if invalid |

**Blocked globally:** any UI control that triggers `--apply`, production import, or public publish.

---

## Privacy and Safety Behavior

1. Optional contact email masked by default in queue and detail.
2. Reveal requires explicit action with audit log entry (proposed).
3. No raw Sheet row dumps or bulk export from UI.
4. Internal notes never in public API responses or client-side analytics.
5. No secrets in browser console, URLs, or error toasts.
6. Evidence and job URLs rendered as links; validate http/https before render.
7. External links: `rel="noopener noreferrer"`, open in new tab.
8. No automatic import on any button or form submit.
9. No `--apply` trigger reachable from UI navigation or keyboard.
10. Rate limiting required on moderation endpoints before public/hosted exposure.
11. Admin-only access until RBAC implemented; 403 for non-admin.
12. CORS must be approved before hosted frontend calls moderation API.

---

## Error and Empty States

| Condition | User message | Recovery |
| --------- | ------------ | -------- |
| No submissions | "No submissions awaiting review." | Adjust filters |
| Backend unavailable | "Unable to reach moderation service." | Retry |
| Unauthorized (401) | Redirect to login | Sign in |
| Forbidden (403) | "You do not have moderation access." | Contact maintainer |
| Malformed report | "This submission has missing required fields." | Decline or escalate |
| Duplicate lookup unavailable | "Duplicate search unavailable; check manually." | Manual URL search in queue |
| Audit unavailable | "Audit history could not be loaded." | Retry; show partial |
| Validation failed | Field-level errors inline | Fix and resubmit |
| Stale data conflict | "This item was updated elsewhere; refresh." | Reload detail |
| Save failed | "Changes could not be saved." | Retry |
| Network timeout | "Request timed out." | Retry |

---

## Accessibility Requirements

Align with existing frontend quality bar and WCAG-oriented practice:

1. Full keyboard navigation for queue, filters, panels, and decision forms.
2. Visible focus rings on interactive elements (match Tailwind focus styles).
3. Semantic headings (`h1` page title, `h2` sections).
4. Explicit `<label>` for every form control.
5. Status badges use text + icon; not color-only (e.g., "PII: confirmed" not green dot alone).
6. Validation errors linked via `aria-describedby`.
7. Sufficient color contrast (4.5:1 body text minimum).
8. No hover-only actions; all actions keyboard-reachable.
9. Data tables: `<th scope="col">` headers; sort announced to screen readers.
10. Modals trap focus and restore on close.

---

## Responsive Layout

### Desktop (primary)

- Queue: full-width table with horizontal scroll for many columns.
- Detail: two-column layout — main content left, action sidebar right.

### Tablet

- Queue: hide lower-priority columns; card list fallback optional.
- Detail: single column; action bar sticky bottom.

### Mobile (fallback)

- Queue: card list only (company, title, status, date).
- Detail: stacked sections; panels as accordion.
- Decision panel: full-screen modal.

### Overflow

- Long URLs truncate with ellipsis + copy button.
- Narrative scrolls in max-height container.

---

## API Dependencies

### Existing APIs (minimal UI possible)

| API | Supports |
| --- | -------- |
| POST `/api/v1/auth/login` | Login gate |
| GET `/api/v1/auth/me` | Admin check |
| GET `/api/v1/moderation/reports` | Queue list (backend reports only) |
| POST `.../verify` | In-app verify action |
| POST `.../dismiss` | In-app dismiss with optional reason |
| GET `/api/v1/reports/{id}` | Partial detail (not moderation-scoped) |

### Proposed APIs (full spec)

| API | Needed for |
| --- | ---------- |
| GET `/api/v1/moderation/reports/{id}` | Detail with job posting + intake fields |
| PATCH `/api/v1/moderation/reports/{id}/review` | Sheet-equivalent fields |
| GET `/api/v1/moderation/duplicates/search` | Duplicate panel |
| GET `/api/v1/moderation/reports/{id}/audit` | Audit panel |
| POST `.../pii-redaction` | PII confirmation |
| Sheet bridge endpoints | Form/Sheet intake queue (out of scope pending decision) |

### Schema changes likely needed

Sheet SOP fields on backend or separate `IntakeSubmission` entity (see Batch 14D).

### Auth / RBAC gaps

Binary `is_admin` only; no moderator or auditor roles; no refresh token persistence in frontend.

### Audit gaps

No audit retrieval API; limited events compared to full wireframe event list.

**Do not claim proposed endpoints exist.**

---

## Testing Plan

Future frontend and integration tests:

| Area | Tests |
| ---- | ----- |
| Queue rendering | Columns, pagination, empty state |
| Detail rendering | Sections, masked email, consent badge |
| Masked contact email | Hidden by default; reveal logs audit (when API exists) |
| PII confirmation gate | import_ready blocked until pii_redacted |
| Decision validation | Decline requires code; duplicate requires duplicate_of |
| Approve rules | Consent + PII required |
| Auth | 401 redirect; 403 forbidden page |
| Audit rendering | Events listed; expand metadata |
| Accessibility | jest-axe or RTL a11y checks on key screens |
| No apply path | No button/link/route triggers import or `--apply` |
| API client | Mock proposed endpoints until implemented |

Existing backend tests in [test_moderation.py](../backend/tests/test_moderation.py) inform in-app verify/dismiss behavior only.

---

## Implementation Boundaries

- **No implementation in Batch 14C.**
- UI implementation requires Batch 14E/F planning and API/schema approval (14D, 14E).
- Staging deployment requires separate infra approval ([render-deployment-plan.md](render-deployment-plan.md)).
- Moderation UI must launch behind admin auth; not linked from public MVP.
- Public MVP (Pages + Form + Sheet) unchanged.
- Live Sheet Gates 11/12 remain **BLOCKED-LIVE** and separate.

---

## Open Questions

1. Final auth provider and session persistence model?
2. Exact role model: moderator vs admin vs auditor permissions?
3. Sheet as source of truth vs backend DB vs bridge mode for v1 UI?
4. Decline reason taxonomy: SOP codes only or extended set in API?
5. Duplicate matching: URL-only v1 or fuzzy company+title from start?
6. Audit log retention period and export policy?
7. Optional contact email reveal: which roles, how logged, any rate limit?
8. `needs_more_info`: internal flag only or reporter contact workflow?
9. First implementation target: local Docker, Render staging, or production?
10. Single app route tree vs separate admin subdomain?

---

## Recommended Next Batches

| Batch | Scope | Type |
| ----- | ----- | ---- |
| **14D** | Moderation schema decision record (Report vs IntakeSubmission) | Docs-only |
| **14E** | Moderation API implementation plan (endpoint rollout order) | Docs-only |
| **14F** | Moderation frontend implementation plan (routes, components, test order) | Docs-only |
| **14A** | Render staging implementation | Deploy — explicit infra approval only |

**Next recommended batch:** **14D** — moderation schema decision record (docs-only).

## Related Documents

- [moderation-ui-scope.md](moderation-ui-scope.md)
- [moderation-api-contract-review.md](moderation-api-contract-review.md)
- [moderation-sop.md](moderation-sop.md)
- [moderation-api.md](moderation-api.md)
- [post-launch-roadmap.md](post-launch-roadmap.md)
