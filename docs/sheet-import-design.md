# Google Sheet Import Pipeline Design

Design document for [Issue #6](https://github.com/codethor0/ghost-sweep/issues/6). Defines how maintainer-approved Google Sheet rows map to PostgreSQL records when a future import script runs (Batch 12A+). **No implementation in Batch 10D.**

Prerequisites:

- [google-form-intake-spec.md](google-form-intake-spec.md) — Form fields
- [moderation-sop.md](moderation-sop.md) — review states and `import_ready` rules
- [moderation-model.md](moderation-model.md) — product moderation principles

## 1. Purpose

Bridge manual Form/Sheet intake to the local (and eventually hosted) PostgreSQL backend without bypassing moderation. The import pipeline:

1. Reads exported or API-fetched Sheet rows marked `import_ready=yes`
2. Validates and normalizes untrusted Sheet data offline
3. Creates or matches `companies`, `job_postings`, and `reports` records
4. Records audit metadata for traceability and idempotency
5. Supports **dry-run** mode before any write

The first implementation must be **local/admin-only** (CLI or maintainer script). It must not expose a public API endpoint.

## 2. Current Google Form fields

From [google-form-intake-spec.md](google-form-intake-spec.md):

| Sheet column (Form label) | Required | Import use |
| ------------------------- | -------- | ---------- |
| Timestamp | auto | `detected_at` / audit metadata |
| Job posting URL | yes | Primary posting key (after normalization) |
| Company name | yes | Company match or create |
| Job title | yes | Job posting title |
| Location or remote | yes | Company `locations` / posting context |
| Date seen | yes | `posted_date` hint / audit metadata |
| Why do you suspect this is a ghost job? | yes | Report `description` body |
| Has the company responded? | yes | Report description prefix (metadata line) |
| Consent | yes | Eligibility gate only (not stored on report) |
| Evidence links | optional | Validated URLs; metadata or description appendix |
| Optional contact email | optional | **Never imported** to backend tables |

## 3. Manual review columns (moderation SOP)

From [moderation-sop.md](moderation-sop.md):

| Column | Import use |
| ------ | ---------- |
| `review_status` | Must be `approved_for_import` |
| `import_ready` | Must be `yes` |
| `reviewer` | Audit metadata (`sheet_reviewer`) |
| `reviewed_at` | Audit metadata |
| `pii_redacted` | Must be `yes` |
| `decline_reason_code` | Must be empty |
| `duplicate_of` | Must be empty |
| `notes` | Audit metadata only (not copied to public description) |
| `escalation_level` | Must be `none` or empty |

Rows failing any eligibility rule are skipped with a logged reason. No partial import of ineligible rows.

## 4. Sheet-to-backend entity mapping

### 4.1 Company (`companies`)

| Sheet / derived input | Backend field | Rule |
| --------------------- | ------------- | ---- |
| Company name | `name` | Trim; match existing by case-insensitive exact name |
| Job posting URL host | `domain` | Extract hostname from normalized URL; set if new company |
| Location or remote | `locations` | Single-element list `[location]` if new company |
| — | `verified_status` | `unverified` |
| — | `integrity_score` | Default (`50.0`); scoring pipeline recalculates after report |
| — | `industry`, `size` | `null` unless added in future Sheet columns |

**Constraint:** `companies.name` is UNIQUE. Import must not create duplicate names differing only by case.

### 4.2 Job posting (`job_postings`)

| Sheet / derived input | Backend field | Rule |
| --------------------- | ------------- | ---- |
| Job posting URL (normalized) | `url` | Store **normalized** URL (unique index) |
| Job posting URL (original) | audit metadata | Preserve as `original_url` in import audit |
| Job title | `title` | Trim; max 255 chars; truncate with audit flag if over |
| Company match/create | `company_id` | FK to matched or created company |
| Date seen | `posted_date` | Parse as timezone-aware datetime if valid |
| Timestamp | `detected_at`, `last_seen_at` | Form submission time |
| URL provider detection | `source` | Map from offline helper (see section 8) |
| — | `status` | `suspected_ghost` for Sheet imports (configurable in script) |
| — | `description` | `null` (narrative lives on report) |
| — | `ghost_risk_score` | Default; recalculate via scoring pipeline |

**Constraint:** `job_postings.url` is UNIQUE. Normalized URL is the dedupe key.

### 4.3 Report (`reports`)

| Sheet / derived input | Backend field | Rule |
| --------------------- | ------------- | ---- |
| Narrative + structured prefix | `description` | See section 10 |
| — | `job_posting_id` | FK to created or matched posting |
| — | `reporter_id` | **`null`** (anonymous Form intake; no user account) |
| Derived from narrative | `report_type` | Default `ghost_job`; see section 10 |
| Moderation decision | `status` | **`pending`** on import (Sheet approval != API verify) |
| — | `confidence_score` | Default `0.0` |
| — | `verification_votes` | `0` |

**Note:** Sheet `approved_for_import` means eligible for database intake, not equivalent to backend `verified`. Moderators still use in-app moderation APIs after import if needed.

### 4.4 Evidence (`evidence_files`)

**v1:** Do not create `evidence_files` rows. Table requires `sha256_hash` and upload workflow (deferred). Validated evidence URLs go to import audit metadata and optional description appendix (section 11).

## 5. Required import eligibility rules

Import a row only when **all** conditions hold:

| # | Rule |
| - | ---- |
| 1 | `review_status` = `approved_for_import` |
| 2 | `import_ready` = `yes` |
| 3 | `pii_redacted` = `yes` |
| 4 | `decline_reason_code` is empty |
| 5 | `duplicate_of` is empty |
| 6 | `escalation_level` is `none` or empty |
| 7 | Consent field indicates checked |
| 8 | Job posting URL present |
| 9 | Company name and job title non-empty |
| 10 | Narrative length >= 20 characters after trim |
| 11 | Normalized job URL is valid http/https |
| 12 | Optional contact email column is **not** written to any backend column |

Skip ineligible rows; record skip reason in dry-run report or import log.

## 6. Deduplication strategy

Three layers:

### 6.1 Sheet row idempotency

Each Sheet row is identified by stable key:

- Preferred: Google Sheet row number + spreadsheet id (export metadata)
- Fallback: hash of (`Timestamp`, normalized URL, company name, job title)

Before creating records, query import audit history (section 16) for this key. If already imported successfully, **skip** (idempotent no-op).

### 6.2 Job posting URL dedupe

1. Normalize URL via `normalize_job_url()` from [job_url_validation.py](../backend/app/services/job_url_validation.py)
2. Look up existing `job_postings.url` = normalized URL
3. If exists: reuse posting; create report only if no prior import for same Sheet row
4. If not exists: create posting

### 6.3 Report dedupe (same posting)

If a report from the same Sheet row already exists (audit metadata match), skip.

If a different Sheet row targets the same posting:

- Allow multiple reports on same posting **only** if Sheet rows differ (different narratives/timestamps)
- Log warning in dry-run for maintainer review

Company name dedupe: case-insensitive match on `companies.name` before insert.

## 7. URL normalization and validation strategy

Treat every URL as untrusted input.

| Step | Function | Outcome |
| ---- | -------- | ------- |
| 1 | Trim whitespace | Reject empty |
| 2 | `normalize_job_url()` | Returns normalized URL or `None` |
| 3 | Reject if `None` | Skip row; reason `invalid_job_url` |
| 4 | `validate_http_https_url()` | Apply to each evidence link |
| 5 | Reject dangerous schemes | `javascript:`, `data:`, `file:`, `mailto:` (Batch 10B parity) |

**No network calls:** Do not fetch URLs to verify they resolve. Offline validation only (Batch 6D / 10B scope).

Store:

- `job_postings.url` = normalized URL (dedupe)
- Audit metadata `original_job_url` = raw Sheet value

## 8. Company matching strategy

```
1. normalized_name = company_name.strip()
2. SELECT company WHERE lower(name) = lower(normalized_name)
3. IF found -> use company_id
4. ELSE -> INSERT company (name=normalized_name, domain=host from URL, locations=[location])
```

Edge cases:

| Case | Action |
| ---- | ------ |
| Same name, different domain | Prefer existing company; log `company_domain_mismatch` warning |
| Normalized name > 255 chars | Skip row |
| Empty company name | Skip row |
| Maintainer flagged in `notes` | Manual review before `import_ready=yes`; import trusts SOP |

Domain extraction: hostname from normalized job URL via `urlsplit`. Do not guess domain from company name alone.

## 9. Job posting matching strategy

```
1. normalized = normalize_job_url(sheet_job_url)
2. IF normalized is None -> skip
3. SELECT job_posting WHERE url = normalized
4. IF found -> reuse id; update last_seen_at if import batch policy allows
5. ELSE -> INSERT with mapped fields (section 4.2)
```

`PostingSource` mapping from `detect_job_source_provider()`:

| JobSourceProvider | PostingSource |
| ----------------- | ------------- |
| WORKDAY, GREENHOUSE, LEVER, ASHBY, SMARTRECRUITERS, COMPANY_CAREERS | `company_site` |
| UNKNOWN | `other` |

Future: finer mapping to `linkedin`, `indeed`, `glassdoor` when URL host patterns are added to the offline helper (Issue #5). v1 uses `company_site` or `other` only.

## 10. Report creation strategy

### Description format

Structured text block (no schema change):

```text
[ghost-sweep Sheet import]
Date seen: {date_seen}
Company responded (reporter): {has_company_responded}
Location: {location}

{narrative}
```

Optional footer if evidence links present:

```text
Evidence links (public URLs):
- {url1}
- {url2}
```

Do not include optional contact email, internal `notes`, or raw Sheet reviewer PII.

### Report type selection

| Condition | `report_type` |
| --------- | ------------- |
| Default | `ghost_job` |
| Narrative keywords (future heuristic) | Map to `no_response`, `repost_loop`, `stale_posting`, etc. |

v1: use `ghost_job` for all Sheet imports unless maintainer adds optional Sheet column `report_type` in a future SOP revision (requires SOP + schema approval).

### Initial report status

Always `pending`. Sheet moderation approval does not auto-verify. In-app moderation (`verify` / `dismiss`) remains a separate step.

## 11. Evidence link handling

1. Split optional Evidence links field on newlines or whitespace
2. Trim each token
3. Validate each with `validate_http_https_url()`
4. Invalid links: omit from description; log in audit metadata `dropped_evidence_urls`
5. Valid links: include in description appendix **and** audit metadata `evidence_urls[]`

Do not insert into `evidence_files` until upload pipeline and hash policy exist.

## 12. Optional email handling and privacy

| Rule | Detail |
| ---- | ------ |
| Never import | Do not create `users` rows from Form email |
| Never store on report | `reporter_id` remains `null` |
| Never store in description | Email must not appear in public-facing text |
| Never store in audit metadata | Avoid accidental log exposure |
| Maintainer follow-up | Use project Google account and Sheet column directly; outside import script |

If email appears in narrative despite SOP, skip row or redact before import (prefer skip + log `pii_in_narrative`).

## 13. Error handling

| Error class | Behavior |
| ----------- | -------- |
| Eligibility failure | Skip row; count as `skipped` |
| Invalid URL | Skip row; reason code |
| Company name too long | Skip row |
| DB unique violation (race) | Roll back row; retry once; then skip with log |
| Partial row failure | Roll back entire row transaction (company + posting + report atomic) |
| Unexpected exception | Abort batch; exit non-zero; no silent continue |

Import script should produce a summary:

```text
processed=N imported=M skipped=K errors=E
```

Each skipped row: sheet_row_id, reason_code, message (no PII).

## 14. Dry-run mode design

Required for first implementation (Batch 12A).

| Mode | DB writes | Output |
| ---- | --------- | ------ |
| `--dry-run` (default) | None | Planned actions per row |
| `--apply` | Yes | Commits + audit logs |

Dry-run output per eligible row:

- Match or create company (preview)
- Match or create job posting (preview normalized URL)
- Report description preview (redacted)
- Dedupe/idempotency decision (would skip / would import)
- Validation warnings

Maintainers must run dry-run and review output before `--apply`.

## 15. Idempotency rules

| Key | Storage (v1) | Behavior on re-run |
| --- | ------------ | ------------------ |
| Sheet row id | `audit_logs.metadata_json.sheet_row_id` | Skip if prior successful import |
| Normalized job URL | `job_postings.url` unique | Reuse posting |
| Import batch id | `audit_logs.metadata_json.import_batch_id` | UUID per run |

Re-import policy:

- Same Sheet row + same data: no-op
- Same Sheet row + changed data after approval: skip; require maintainer manual fix in Sheet (new row or revert `import_ready`)
- Same URL + new Sheet row: new report allowed if narrative differs

**Future (schema approval):** dedicated `sheet_import_runs` and `sheet_import_rows` tables for cleaner idempotency. Not in v1.

## 16. Audit logging expectations

Use existing `audit_logs` table. Import actor: admin user running CLI (`actor_user_id` set) or `null` with `metadata_json.actor=sheet_import_script`.

### Per successful import

| action | entity_type | entity_id | metadata_json (minimum) |
| ------ | ----------- | --------- | ------------------------- |
| `sheet_import.row_imported` | `report` | report.id | `sheet_row_id`, `spreadsheet_id`, `import_batch_id`, `original_job_url`, `normalized_job_url`, `sheet_reviewer`, `sheet_reviewed_at`, `form_timestamp`, `evidence_urls` |
| `report.created` | `report` | report.id | Existing fields + `source=sheet_import` |
| `company.created` | `company` | company.id | If new: `sheet_row_id`, `import_batch_id` |
| `job_posting.created` | `job_posting` | posting.id | If new: `original_job_url`, `normalized_job_url`, `sheet_row_id` |

Extend `log_report_created` or add `log_sheet_import` helper in a future batch (requires code approval).

Scoring pipeline: call `recalculate_for_job_posting_and_company()` after each imported report (matches existing `create_report` behavior).

## 17. Security and privacy risks

| Risk | Mitigation |
| ---- | ---------- |
| Untrusted Sheet data | Offline validation; eligibility gates; no scraping |
| PII in narrative | SOP `pii_redacted=yes`; skip if detected |
| Email leakage | Never import email fields |
| XSS in stored text | Reports are API text; frontend must escape (existing) |
| Dangerous URLs | `validate_http_https_url()` on all URLs |
| Credential exposure in Sheet export | Restrict Sheet access; do not commit exports to repo |
| Import script credentials | Google API tokens in env only; never in repo |
| Privilege escalation | Local/admin-only; no public endpoint |
| Duplicate flooding | URL dedupe + Sheet row idempotency |

Google Sheet is **untrusted input** even though maintainers review it. Formula injection in CSV export is a risk; use API or sanitized export; do not execute Sheet formulas in import script.

## 18. Future automation phases

| Phase | Batch | Scope |
| ----- | ----- | ----- |
| **10D** | This doc | Design only |
| **12A** | Import dry-run CLI | Dry-run only; CSV export; no DB writes |
| **12B** | Import apply mode | Local Docker; `--apply`; audit logs; see [sheet-import-apply-design.md](sheet-import-apply-design.md) |
| **12C** | Scheduled import | Maintainer-triggered or cron; still admin-only |
| **13A** | Hosted import | Runs against production DB with approval |
| **13B** | Moderation UI link | Show Sheet origin on imported reports |
| **Future** | Evidence files | Upload pipeline + link evidence URLs to `evidence_files` |
| **Future** | Auto Sheet poll | Google Sheets API polling; requires OAuth and security review |

Each phase requires maintainer approval. Schema changes (import tracking tables) require separate approval per AGENTS.md.

## 19. Explicit non-goals

- No scraping or live HTTP fetches to job boards
- No auto-verify of reports on import (`verified` status)
- No public API endpoint for import
- No import of optional contact email
- No import of rows without `import_ready=yes`
- No import of declined, escalated, or unreviewed rows
- No `evidence_files` rows in v1
- No Google Form or Sheet URL changes
- No modification to public MVP HTML
- No new dependencies in design batch (implementation batch must request approval)
- No automatic company verification or employer claims
- No replacement of Google Form intake

## Related documents

- [sheet-import-apply-design.md](sheet-import-apply-design.md) — Batch 12B apply-mode design gate
- [moderation-sop.md](moderation-sop.md)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [post-launch-roadmap.md](post-launch-roadmap.md) — Track 1
- [moderation-model.md](moderation-model.md)
- [legal-risk.md](legal-risk.md)
- [implementation-status.md](implementation-status.md)

## Approval checklist (maintainer)

Before Batch 12A implementation:

- [ ] Field mapping approved
- [ ] `pending` vs `verified` policy approved
- [ ] Description format approved
- [ ] Idempotency strategy approved (audit-only v1)
- [ ] Dry-run default approved
- [ ] PostingSource mapping v1 approved
- [ ] Schema change needs identified (if any)

Batch 12A dry-run CLI shipped. Before Batch 12B `--apply` implementation, see [sheet-import-apply-design.md](sheet-import-apply-design.md) approval checklist (section 18).
