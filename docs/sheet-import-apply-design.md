# Sheet Import Apply Mode Design (Batch 12B)

Design gate for [Issue #6](https://github.com/codethor0/ghost-sweep/issues/6). Defines controlled `--apply` behavior for the Sheet import CLI **before any implementation code is written**.

Prerequisites (complete):

- [sheet-import-design.md](sheet-import-design.md) — parent pipeline design (Batch 10D)
- [sheet_import.py](../backend/app/services/sheet_import.py) — Batch 12A dry-run planner
- [scripts/sheet_import_dry_run.py](../scripts/sheet_import_dry_run.py) — dry-run CLI
- [scripts/verify_sheet_columns.py](../scripts/verify_sheet_columns.py) — column verification
- [backend/tests/fixtures/sheet_import_sample.csv](../backend/tests/fixtures/sheet_import_sample.csv) — sanitized fixture

**This document is design-only.** No `--apply` implementation, schema change, or API change is authorized until the maintainer approval gates in section 18 are signed.

## 1. Purpose

Batch 12A proved that Sheet rows can be validated and planned offline with no database access. Batch 12B adds a **local/admin-only write path** that:

1. Reuses the same eligibility and planning logic as dry-run
2. Persists `companies`, `job_postings`, and `reports` inside per-row transactions
3. Records audit metadata for traceability and idempotency
4. Recalculates scoring after each imported report
5. Never exposes import as a public API endpoint

The launch architecture remains unchanged:

```text
GitHub Pages -> Google Form -> Google Sheet -> manual review -> local import CLI -> PostgreSQL (Docker)
```

## 2. CLI surface (planned)

Extend [scripts/sheet_import_dry_run.py](../scripts/sheet_import_dry_run.py) or add a sibling script `scripts/sheet_import_apply.py`. Preferred: **single script** with explicit mode flags to keep parity in one code path.

| Flag | Default | Behavior |
| ---- | ------- | -------- |
| (none) | yes | Dry-run only (Batch 12A behavior; no DB writes) |
| `--apply` | off | Perform database writes for eligible rows |
| `--actor-user-id UUID` | unset | Optional maintainer user id for audit `actor_user_id` |
| `--import-batch-id UUID` | auto-generated | Override batch id for audit grouping |
| `--spreadsheet-id TEXT` | unset | Optional Sheet id stored in audit metadata |
| `--show-descriptions` | off | Print planned/imported report descriptions |

Safety gates for `--apply`:

| Gate | Rule |
| ---- | ---- |
| Explicit flag | `--apply` required; default remains dry-run |
| Local DB only | Refuse when `ENVIRONMENT` is not `development` or `test` |
| Missing SOP columns | Exit non-zero before any write (same as dry-run) |
| No confirmation prompt in v1 | Maintainer runs dry-run first; `--apply` is the confirmation |

Future (not v1): interactive `--confirm` prompt or `--dry-run-diff` against prior batch.

## 3. Apply eligibility rules

Apply mode uses **exactly** the same rules as dry-run via `check_eligibility()` in [sheet_import.py](../backend/app/services/sheet_import.py). No additional apply-only bypasses.

A row is eligible for apply when **all** conditions hold (mirrors [sheet-import-design.md](sheet-import-design.md) section 5):

| # | Rule | Skip reason code |
| - | ---- | ---------------- |
| 1 | `review_status` = `approved_for_import` | `review_status` |
| 2 | `import_ready` = `yes` | `import_ready` |
| 3 | `pii_redacted` = `yes` | `pii_redacted` |
| 4 | `decline_reason_code` empty | `decline_reason_code` |
| 5 | `duplicate_of` empty | `duplicate_of` |
| 6 | `escalation_level` is `none` or empty | `escalation_level` |
| 7 | Consent field indicates checked | `no_consent` |
| 8 | Job posting URL present | `missing_job_url` |
| 9 | Company name non-empty, <= 255 chars | `missing_company_name` / `company_name_too_long` |
| 10 | Job title non-empty | `missing_job_title` |
| 11 | Narrative >= 20 characters after trim | `narrative_too_short` |
| 12 | No email address in narrative | `pii_in_narrative` |
| 13 | Normalized job URL is valid http/https | `invalid_job_url` |

Additional apply-only gates (after eligibility, before write):

| # | Rule | Skip reason code |
| - | ---- | ---------------- |
| 14 | Row not previously imported (idempotency) | `already_imported` |
| 15 | Dry-run plan action is `would_import` (parity check) | internal error if mismatch |

Ineligible rows are **skipped with no writes**. Apply never downgrades or overrides Sheet moderation fields.

## 4. Transaction boundaries

### Per-row atomic unit

Each eligible row is one **atomic database unit**. Within a single row import, all of the following succeed or none persist:

| Step | Entity / action |
| ---- | --------------- |
| 1 | Idempotency pre-check (read-only) |
| 2 | Company match or create |
| 3 | Job posting match or create (or reuse) |
| 4 | Report create |
| 5 | Company counter updates (`report_count`, optionally `total_postings`) |
| 6 | Audit log entries |
| 7 | Scoring recalculation |
| 8 | Commit |

Implementation pattern:

```text
for each row:
    plan = plan_row_import(row)          # offline, same as dry-run
    if plan.action == "skip":
        record skip; continue
    if already_imported(plan):
        record skip; continue
    async with session.begin():         # one transaction per row
        execute plan writes
        write audit logs
        recalculate scores
    # commit on context exit
```

### Batch-level behavior

| Scope | Policy |
| ----- | ------ |
| Per-row failure (expected) | Roll back that row; log skip/error; continue remaining rows |
| Per-row failure (IntegrityError race) | Roll back; retry once; then skip with `unique_violation` |
| Unexpected exception mid-batch | Abort remaining rows; exit non-zero; prior successful rows **remain committed** |
| CSV parse / header failure | No writes; exit non-zero before loop |

Rationale: a maintainer import batch may contain hundreds of rows. One bad row should not undo successfully imported rows. Within a row, partial company/posting/report creation is forbidden.

### Session management

- Use `SessionLocal()` from [database.py](../backend/app/database.py) (async)
- Do not reuse API dependency injection (`get_db_session`)
- CLI owns session lifecycle; no HTTP request scope

## 5. Idempotency

v1 uses **existing `audit_logs` JSONB metadata** — no new tables in Batch 12B (schema change deferred).

### Row identity key

Primary key (v1):

```text
row_fingerprint = sha256(timestamp | normalized_url | company_name | job_title)[:16]
```

Already computed by `_row_fingerprint()` in Batch 12A. Stored in audit metadata as `sheet_row_fingerprint`.

Secondary key (when available):

```text
sheet_row_number = CSV line number (1-based data row; header excluded)
```

Stored as `sheet_row_number` in audit metadata. CSV re-exports may shift row numbers; fingerprint is the stable fallback.

Optional metadata (maintainer-supplied):

- `spreadsheet_id` — Google Sheet document id
- `import_batch_id` — UUID generated once per CLI invocation

### Idempotency check (before write)

```sql
SELECT 1 FROM audit_logs
WHERE action = 'sheet_import.row_imported'
  AND metadata->>'sheet_row_fingerprint' = :fingerprint
LIMIT 1
```

If found: skip row with `already_imported`. Do not create duplicate reports for the same Sheet row.

### Re-import policy

| Scenario | Behavior |
| -------- | -------- |
| Same row, same fingerprint, prior success | Skip (`already_imported`) |
| Same row, changed data after approval | Skip; maintainer must fix Sheet (new row or reset workflow) |
| Same normalized URL, different Sheet row | Allow new report if fingerprint differs |
| Same URL, same fingerprint | Skip via row idempotency |

### Future (requires schema approval)

Dedicated `sheet_import_runs` and `sheet_import_rows` tables per [sheet-import-design.md](sheet-import-design.md) section 15. Not in Batch 12B scope.

## 6. Company matching and creation

Reuse parent design section 8. Implementation lives in a new service function (e.g. `match_or_create_company_for_sheet_row`).

```text
1. normalized_name = company_name.strip()
2. SELECT company WHERE lower(name) = lower(normalized_name)
3. IF found:
     use company_id
     IF existing.domain IS NOT NULL AND host from URL differs:
       log warning company_domain_mismatch (audit metadata + CLI output)
     do NOT update existing company name or domain in v1
4. ELSE:
     INSERT company (
       name=normalized_name,
       domain=hostname from normalized job URL (lowercase),
       locations=[location from Sheet] if non-empty else [],
       verified_status=unverified,
       integrity_score=50.0
     )
     increment audit: company.created
```

Constraints:

- `companies.name` is UNIQUE — case-insensitive match before insert
- Name > 255 chars: caught by eligibility; never reaches apply
- Empty domain if URL has no hostname: allow `domain=null`; log warning

Counter updates on new company create: none beyond defaults (`total_postings=0`, `report_count=0`).

## 7. Job posting matching and creation

Reuse parent design section 9.

```text
1. normalized = plan.normalized_job_url  (from plan_row_import)
2. SELECT job_posting WHERE url = normalized
3. IF found:
     reuse posting.id
     optionally update last_seen_at = form Timestamp (parsed) in v1
     do NOT change title, company_id, or status in v1
4. ELSE:
     INSERT job_posting (
       company_id=matched company,
       title=job_title trimmed to 255 chars,
       url=normalized,
       source=from _map_posting_source(),
       posted_date=parsed Date seen if valid else null,
       status=suspected_ghost,
       description=null,
       ghost_risk_score=50.0,
       detected_at=parsed Timestamp or utcnow(),
       last_seen_at=same as detected_at
     )
     increment company.total_postings
     audit: job_posting.created
```

Posting status: use `PostingStatus.SUSPECTED_GHOST` for new Sheet imports (aligns with parent design section 4.2). Existing matched postings keep their current status in v1.

Title truncation: if > 255 chars, truncate with audit flag `job_title_truncated_to_255` (already a dry-run warning).

Date parsing: best-effort parse of Form `Timestamp` and `Date seen`; invalid values -> `null` with audit warning `date_parse_failed`. No timezone guessing beyond ISO-like and common Sheet export formats.

## 8. Report creation

Reuse parent design section 10.

```text
INSERT report (
  job_posting_id=matched or created posting,
  reporter_id=null,
  report_type=ghost_job,
  description=plan.description_preview,
  status=pending,
  confidence_score=0.0,
  verification_votes=0
)
increment company.report_count
audit: report.created + sheet_import.row_imported
recalculate_for_job_posting_and_company()
```

Description format is **identical** to `_build_description()` output used in dry-run. Apply must call the same builder; no apply-only description template.

Report status is always `pending`. Sheet `approved_for_import` does not auto-verify. In-app moderation remains separate.

## 9. Evidence URL handling

Identical to Batch 12A / parent design section 11:

1. Split Evidence links field on whitespace/commas/semicolons
2. Validate each with `validate_http_https_url()`
3. Invalid links: omit from description; record in audit metadata `dropped_evidence_urls[]`
4. Valid links: included in description appendix and audit metadata `evidence_urls[]`

No `evidence_files` rows in v1.

Apply output must report dropped evidence count (same as dry-run `dropped_evidence=N`).

## 10. Optional email exclusion

Hard rule (unchanged from SOP and Batch 12A):

| Rule | Detail |
| ---- | ------ |
| Never read into apply logic | Optional contact email column is ignored after header mapping |
| Never store | No backend column, no audit metadata, no description |
| Never log | CLI skip/import lines must not print email values |
| Narrative email | Eligibility rejects via `pii_in_narrative` |

Apply implementation must not add code paths that reference `optional_contact_email` except to document exclusion in module docstring.

## 11. Audit logging events

Extend [audit.py](../backend/app/services/audit.py) with Sheet-import-specific helpers. Do not overload `log_report_created()` (requires non-null `actor_user_id` tied to API reporter).

### New audit actions (v1)

| action | entity_type | entity_id | When |
| ------ | ----------- | --------- | ---- |
| `sheet_import.batch_started` | `sheet_import` | import_batch_id (UUID) | Once at apply start |
| `sheet_import.row_imported` | `report` | report.id | Successful row import |
| `sheet_import.row_skipped` | `sheet_import` | import_batch_id | Optional: skipped rows (reason codes only) |
| `sheet_import.batch_completed` | `sheet_import` | import_batch_id | Once at apply end |
| `company.created` | `company` | company.id | New company only |
| `job_posting.created` | `job_posting` | posting.id | New posting only |
| `report.created` | `report` | report.id | Every import; includes `source=sheet_import` |

### `sheet_import.row_imported` metadata (minimum)

```json
{
  "import_batch_id": "uuid",
  "sheet_row_number": 2,
  "sheet_row_fingerprint": "c25da56b778c1f7f",
  "spreadsheet_id": "optional",
  "original_job_url": "raw sheet value",
  "normalized_job_url": "https://...",
  "sheet_reviewer": "maintainer",
  "sheet_reviewed_at": "2026-07-01",
  "form_timestamp": "2026-07-01 12:00:00",
  "evidence_urls": ["https://example.com/archive"],
  "dropped_evidence_urls": [],
  "warnings": [],
  "company_action": "matched|created",
  "posting_action": "matched|created",
  "source": "sheet_import"
}
```

### Actor identity

| `--actor-user-id` | `actor_user_id` | `metadata_json.actor` |
| ----------------- | --------------- | --------------------- |
| Provided valid UUID | that user id | omitted |
| Omitted | `null` | `"sheet_import_script"` |

If provided, UUID must exist in `users` table; otherwise exit non-zero before batch (fail fast).

Skipped-row audit entries (`sheet_import.row_skipped`) are optional in v1 to limit log volume; CLI summary is required. Successful imports must always emit `sheet_import.row_imported`.

## 12. Dry-run vs apply output parity

Apply mode must use `plan_row_import()` as the single planning source. No parallel mapping logic.

| Dry-run output | Apply output |
| -------------- | ------------ |
| `WOULD_IMPORT` | `IMPORTED report_id=... company_id=... posting_id=...` |
| `SKIP reason=...` | `SKIP reason=...` (identical) |
| `fingerprint=...` | same fingerprint |
| `dropped_evidence=N` | same |
| `warnings=...` | same |
| `SUMMARY processed=N would_import=M skipped=K` | `SUMMARY processed=N imported=M skipped=K errors=E` |

Parity verification (implementation batch):

- For every row, `plan.action` before apply matches outcome
- `description_preview` in DB equals dry-run preview for imported rows
- Unit test: run `plan_row_import` and apply path on fixture; assert same skip/import decisions

Recommended workflow for maintainers:

```bash
python3.11 scripts/verify_sheet_columns.py export.csv
python3.11 scripts/sheet_import_dry_run.py export.csv
python3.11 scripts/sheet_import_dry_run.py export.csv --apply
```

## 13. Rollback and failure behavior

| Failure class | Row TX | Batch | Exit code |
| ------------- | ------ | ----- | --------- |
| Eligibility skip | n/a | continue | 0 if no other errors |
| Idempotency skip | n/a | continue | 0 |
| Unique violation (company/posting) | rollback; retry once | continue | 0 if retry succeeds |
| Unique violation after retry | rollback | continue | 0; count as skip |
| FK / validation error | rollback | continue | 0; count as error skip |
| DB connection loss | rollback | abort | non-zero |
| Uncaught exception | rollback | abort | non-zero |
| Missing SOP columns | no writes | abort | non-zero |

Retry policy: one retry per row on `IntegrityError` only (concurrent import race). No exponential backoff in v1.

Error output: print `row=N ERROR reason=... message=...` without PII. Include `import_batch_id` in final summary for log correlation.

## 14. Duplicate row handling

Three layers:

### Sheet-level duplicates

Rows with non-empty `duplicate_of` fail eligibility (`duplicate_of` reason). Apply never imports them.

Maintainer resolves duplicates in Sheet before setting `import_ready=yes`.

### URL-level duplicates

Normalized job URL is UNIQUE on `job_postings.url`. Second Sheet row with same URL but different fingerprint:

- Reuse existing posting
- Create new report (allowed if narratives differ)
- Log CLI warning `same_posting_multiple_reports`

### Import-level duplicates

Same `sheet_row_fingerprint` with prior `sheet_import.row_imported` audit entry:

- Skip with `already_imported`
- No new report, no counter changes

## 15. Partial import prevention

| Level | Prevention |
| ----- | ---------- |
| Within one row | Single transaction; company + posting + report + audit + counters + scoring commit together |
| Across entities | No report without posting; no posting without company; no orphan audit without entity |
| Counter integrity | `company.report_count` and `total_postings` updated in same transaction as entity create |
| Scoring | `recalculate_for_job_posting_and_company()` inside row transaction before commit |

Partial import **across rows** is allowed by design: row 5 failing does not roll back rows 1-4. Maintainers use `import_batch_id` to audit partial batches.

If full-batch atomicity is required in future, add `--single-transaction` flag (non-goal for v1).

## 16. Local/admin-only execution

| Requirement | Implementation |
| ----------- | -------------- |
| No public API route | CLI script only |
| No Google API in v1 | CSV file input only (maintainer export) |
| Local Docker DB | Refuse apply when `ENVIRONMENT=production` |
| No CI invocation | Apply not wired into GitHub Actions |
| No hosted DB without approval | Batch 13A scope |
| Credentials | `DATABASE_URL` from local `.env`; never in repo |
| Sheet exports | Never commit real exports; fixture is sanitized sample only |

Environment guard (planned):

```python
if settings.environment not in {"development", "test"}:
    raise SystemExit("sheet import --apply is local-only")
```

Test environment allows apply against `ghost_sweep_test` for integration tests.

## 17. Test plan (implementation batch)

All tests use `TEST_DATABASE_URL`; no real Sheet data.

### Unit tests (extend `test_sheet_import.py`)

| Test | Asserts |
| ---- | ------- |
| `test_apply_skips_ineligible_row` | No DB rows created |
| `test_apply_creates_company_posting_report` | Full chain persisted |
| `test_apply_matches_existing_company_by_name` | No duplicate company |
| `test_apply_reuses_existing_posting_by_url` | Posting count unchanged |
| `test_apply_idempotent_second_run` | Second run skips with `already_imported` |
| `test_apply_never_stores_optional_email` | Email column absent from all tables |
| `test_apply_description_matches_dry_run` | Byte-equal description |
| `test_apply_truncates_long_job_title` | 255 char title + warning |
| `test_apply_drops_invalid_evidence_urls` | Audit metadata lists dropped URLs |

### Integration tests

| Test | Asserts |
| ---- | ------- |
| `test_apply_fixture_csv` | Sample fixture: 1 imported, 1 skipped |
| `test_apply_audit_log_chain` | `sheet_import.row_imported` + `report.created` present |
| `test_apply_recalculates_scores` | Scores change after import |
| `test_apply_rollback_on_simulated_failure` | Mock mid-row failure; no partial entities |

### CLI tests

| Test | Asserts |
| ---- | ------- |
| `test_cli_apply_requires_flag` | Default invocation writes nothing |
| `test_cli_apply_refuses_production_env` | Exit non-zero |
| `test_cli_apply_output_format` | IMPORTED line includes ids |

### Manual maintainer checklist (pre-production apply)

1. Export live Sheet to CSV (do not commit)
2. `verify_sheet_columns.py`
3. Dry-run review
4. Apply against local Docker
5. Verify reports in DB and audit logs
6. Reset local DB or use test DB for repeat drills

Coverage gate: maintain >= 80% backend coverage after implementation.

## 18. Explicit approval gates before code

Implementation of Batch 12B is **blocked** until maintainer signs each item.

Batch 12G update (2026-07-02): Google live Sheet automation failed across all attempted paths. A local fallback sanitized artifact outside the repo passed verification scripts, but **final Section 18 sign-off is not ready**. The fallback artifact proves the importer accepts the intended 20-column shape and valid consent path, but it does not replace live Sheet verification.

Batch 12F-P / docs Batch 12Q update (2026-07-02): Offline post-upload artifact verification **PASS** (processed=2, would_import=1, skipped=1 on generated offline CSV). Offline artifact Gates 11 and 12 are **READY**. This is **OFFLINE-PASS only**, not live Google Sheet proof. Live Gates 11 and 12 remain **BLOCKED-LIVE** until verification passes on a CSV exported from the live Sheet.

Batch 12S maintainer decision (2026-07-02): **Section 18 amended for MVP readiness.** Offline importer gate **ACCEPTED-MVP** based on Batch 12F-P evidence. Live Google Sheet export proof **deferred**. Live Gates 11 and 12 remain **BLOCKED-LIVE**. This does **not** claim live Sheet proof passed, production import is enabled, or `--apply` is ready.

**SECTION 18 AMENDED FOR MVP:**

- Offline importer gate accepted (Batch 12F-P).
- Live Google Sheet export proof deferred.
- Live proof remains required before production automation or `--apply` mode.
- MVP readiness may proceed under amended offline gate language only.

Do not implement `--apply` until explicitly approved in a later maintainer decision. Live export proof remains required before production Sheet import automation.

| # | Gate | Status |
| - | ---- | ------ |
| 1 | Apply eligibility matches dry-run (no bypass) | Pending |
| 2 | Per-row transaction boundary approved | Pending |
| 3 | Idempotency via `audit_logs` JSONB (no new tables) approved | Pending |
| 4 | `PostingStatus.SUSPECTED_GHOST` for new postings approved | Pending |
| 5 | Report status `pending` on import approved | Pending |
| 6 | Optional email never stored approved | Pending |
| 7 | Audit action names and metadata schema approved | Pending |
| 8 | Partial batch commit (row isolation) approved | Pending |
| 9 | Local-only `ENVIRONMENT` guard approved | Pending |
| 10 | No schema migration in 12B confirmed | Pending |
| 11 | Offline Sheet columns verified (Batch 12F-P artifact) | ACCEPTED-MVP |
| 11-live | Live Sheet columns verified via `verify_sheet_columns.py` | BLOCKED-LIVE |
| 12 | Offline dry-run reviewed (Batch 12F-P artifact) | ACCEPTED-MVP |
| 12-live | Live dry-run reviewed on latest live export before first apply | BLOCKED-LIVE |

Schema change (`sheet_import_runs` tables) requires a **separate** approval and batch if idempotency via audit logs proves insufficient.

## 19. Non-goals (Batch 12B)

- No Google Sheets API polling or OAuth
- No public HTTP import endpoint
- No auto-verify (`verified` status) on import
- No `evidence_files` rows
- No import of optional contact email
- No modification to Google Form or Sheet URLs
- No public MVP HTML changes
- No frontend, extension, Docker, or CI workflow changes
- No new Python dependencies without approval
- No hosted/production DB apply (Batch 13A)
- No Sheet column schema changes
- No update of existing company domain or posting title on match
- No full-batch single-transaction mode
- No automatic post-import Sheet write-back (`import_ready=no` must be manual in v1)

## 20. Implementation outline (future batch)

When approved, expected code changes (not in this batch):

| Area | Change |
| ---- | ------ |
| `backend/app/services/sheet_import.py` | Add async apply functions; reuse planners |
| `backend/app/services/audit.py` | Add `log_sheet_import_*` helpers |
| `scripts/sheet_import_dry_run.py` | Add `--apply` flag and DB session wiring |
| `backend/tests/test_sheet_import.py` | Apply integration tests |
| Docs | Update implementation-status after ship |

Estimated scope: one service module extension, one audit extension, CLI flag wiring, ~15 tests. No Alembic migration if audit-log idempotency holds.

## Related documents

- [sheet-import-design.md](sheet-import-design.md)
- [moderation-sop.md](moderation-sop.md)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [implementation-status.md](implementation-status.md)
- [post-launch-roadmap.md](post-launch-roadmap.md)
- [implementation-readiness-report.md](implementation-readiness-report.md)
