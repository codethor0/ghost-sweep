# Implementation Readiness Report

Post-roadmap checkpoint after Batches 10A--10D. **Read-only review; no application code changes.** Generated at commit `3b76e34`.

## Batch 12C status update (2026-07-01)

This report is a historical 10E checkpoint. Current state on `main`:

| Area | Status |
| ---- | ------ |
| Live public MVP | Healthy |
| Batch 12A dry-run CLI | **Shipped** |
| Batch 12B apply-mode design | **Shipped** |
| `--apply` implementation | **Not implemented** — blocked on [sheet-import-apply-design.md](sheet-import-apply-design.md) section 18 |
| Live Google Sheet CSV export verify | **Maintainer required** before apply mode |
| Issue #6 | Open — tracks apply implementation |

See [implementation-status.md](implementation-status.md) for current batch history.

Purpose: confirm issue tracker state, doc alignment, live MVP health, and prerequisites before Batch 12A (Sheet import CLI) or Batch 11A (hosting spike).

## Executive summary

| Area | Status |
| ---- | ------ |
| Live public MVP | Healthy |
| Documentation chain (Form -> SOP -> import design) | Aligned in repo |
| Live Google Sheet columns | **Maintainer verify required** (not accessible from repo) |
| Batch 12A import CLI | **Shipped** (dry-run only) |
| Batch 12B apply design | **Shipped** (docs only) |
| `--apply` implementation | **Blocked** — section 18 gates pending |
| Recommended next batch | **12B impl** after gate approval, or Issue #1 / #4 hygiene |

Planning docs are complete through import design. Implementation should wait for maintainer sign-off on [sheet-import-design.md](sheet-import-design.md) approval checklist and optional Sheet column audit.

## Repo checkpoint

| Item | Value |
| ---- | ------- |
| HEAD | `3b76e34e66db96a9344bced55d234f93e0b29cf2` |
| Message | `docs(batch-10d): design Sheet import pipeline` |
| Branch | `main` aligned with `origin/main` |
| Working tree | Clean |
| CI (latest) | success — run 28552106629 |
| Pages | success — built |

## Live site verification

| Check | Result |
| ----- | ------ |
| https://codethor0.github.io/ghost-sweep/ | HTTP 200 |
| Form URL `https://forms.gle/PsjaYrbrCjAgZXjW8` | 2 occurrences |
| Forbidden phrases (blocked, placeholder, localhost, Batch 6C) | Absent |
| Root mirror vs `public-mvp/index.html` | Match |

Live site is consistent with documented public MVP state.

## Issue tracker review

Six issues open: #1, #4, #5, #6, #7, #8.

### Issue #1 — Contributor onboarding: job URL validation pipeline

| Field | Assessment |
| ----- | ---------- |
| State | **Keep OPEN** |
| Rationale | Reframed good-first lane; Batch 6D foundation shipped |
| Scope remaining | Extend offline tests/docs; no API wiring |
| Blocks 12A? | No |

**Recommendation:** Keep open as contributor entry point. Optional: remove stale `batch-6e` label in favor of `good first issue` only.

### Issue #4 — Dependency hardening: deferred npm and pip advisories

| Field | Assessment |
| ----- | ---------- |
| State | **Eligible to close** (maintainer decision) |
| Rationale | Batch 7E classified remaining findings as accepted deferred or local-environment noise per [dependency-audit.md](dependency-audit.md) |
| Scope remaining | Periodic re-audit when dependencies change |
| Blocks 12A? | No |

**Recommendation:** Close with comment linking Batch 7E section, or rename to "Periodic dependency re-audit" and remove `blocked:external`. Do not claim zero advisories exist — accepted risk is documented.

### Issue #5 — Design review: future URL validation API integration

| Field | Assessment |
| ----- | ---------- |
| State | **Keep OPEN** |
| Rationale | Design gate before API wiring, Sheet import validation policy, and extension handoff |
| Scope remaining | Answer where validation runs (import vs report create vs moderation) |
| Blocks 12A? | **Soft block** — import design references offline validation only; 12A can proceed without #5 if scope stays offline |

**Recommendation:** Keep open. Resolve before Batch 11B (URL validation API wiring). Optional: narrow 12A to offline validation only (already in design).

### Issue #6 — Plan: Google Sheet to backend import pipeline

| Field | Assessment |
| ----- | ---------- |
| State | **Keep OPEN** (design phase complete) |
| Rationale | Batch 10D delivered [sheet-import-design.md](sheet-import-design.md); comment at `3b76e34` |
| Scope remaining | Batch 12A CLI implementation |
| Blocks 12A? | N/A — this issue tracks the pipeline |

**Recommendation:** Keep open until 12A ships. Update labels: consider removing `blocked:needs-design` (design done); add note that implementation is blocked on maintainer approval checklist.

### Issue #7 — Form/Sheet moderation workflow and future product UI

| Field | Assessment |
| ----- | ---------- |
| State | **Keep OPEN** (operational SOP complete) |
| Rationale | Batch 10C delivered [moderation-sop.md](moderation-sop.md) |
| Scope remaining | Product moderation UI, Sheet-to-backend bridge UI |
| Blocks 12A? | No — SOP is sufficient for manual review |

**Recommendation:** Keep open for product UI milestones. Optional: edit issue body to mark deliverables 1--2 complete and link SOP; leave deliverable 3 (product UI) open.

### Issue #8 — Extension API wiring plan

| Field | Assessment |
| ----- | ---------- |
| State | **Keep OPEN** |
| Rationale | No design doc yet (Track 3 deliverables pending) |
| Scope remaining | Extension handoff UX plan |
| Blocks 12A? | No |

**Recommendation:** Keep open. Schedule design batch (10F or parallel to 11A) before extension network calls.

### Close summary

| Issue | Recommendation |
| ----- | -------------- |
| #1 | Keep open |
| #4 | **Close or reframe** (maintainer approval) |
| #5 | Keep open |
| #6 | Keep open (design done) |
| #7 | Keep open (SOP done; UI deferred) |
| #8 | Keep open |

## Google Sheet column alignment

Repo docs define expected columns. **The live Sheet was not inspected in this checkpoint** (maintainer-only access). Manual verification required.

### Form columns (from [google-form-intake-spec.md](google-form-intake-spec.md))

Timestamp, Job posting URL, Company name, Job title, Location or remote, Date seen, Why do you suspect..., Has the company responded?, Consent, Evidence links (optional), Optional contact email (optional).

### Maintainer columns (from [moderation-sop.md](moderation-sop.md))

| Column | Referenced in import design |
| ------ | --------------------------- |
| `review_status` | Yes — eligibility gate |
| `reviewer` | Yes — audit metadata |
| `reviewed_at` | Yes — audit metadata |
| `decline_reason_code` | Yes — must be empty for import |
| `duplicate_of` | Yes — must be empty for import |
| `notes` | Yes — audit only |
| `pii_redacted` | Yes — must be `yes` |
| `import_ready` | Yes — must be `yes` |
| `escalation_level` | Yes — must be none/empty |

### Maintainer action item

Open the project Google Sheet and confirm:

1. All nine maintainer column headers exist with exact names (case-sensitive).
2. Data validation or dropdowns match SOP allowed values where practical.
3. At least one test row exercises `approved_for_import` + `import_ready=yes` for future dry-run testing.
4. Optional contact email column is not referenced in any import-ready test row metadata exports.

**Gap:** [post-launch-roadmap.md](post-launch-roadmap.md) Track 1 still mentions only `review_status`, `reviewer`, `notes` in one line — superseded by moderation SOP (cosmetic doc drift).

## Documentation chain

```text
google-form-intake-spec.md  -->  Form fields
moderation-sop.md           -->  Review columns + import_ready gates
sheet-import-design.md      -->  Backend mapping + 12A prerequisites
post-launch-roadmap.md      -->  Batch sequence
implementation-status.md    -->  Batch history
```

Cross-links verified in repo. No contradictions found on import eligibility rules.

## Batch 12A prerequisites

From [sheet-import-design.md](sheet-import-design.md) maintainer approval checklist:

| Prerequisite | Status |
| ------------ | ------ |
| Field mapping approved | Pending maintainer |
| `pending` vs `verified` on import policy approved | Pending maintainer |
| Description format approved | Pending maintainer |
| Idempotency strategy (audit-only v1) approved | Pending maintainer |
| Dry-run default approved | Pending maintainer |
| PostingSource mapping v1 approved | Pending maintainer |
| Schema change needs identified | Documented as optional future tables; v1 uses audit_logs only |
| Live Sheet columns match SOP | **Pending maintainer verify** |
| Local Docker stack validated | Available (existing gates) |
| Issue #5 URL validation API design | Not required if 12A stays offline-only per design |

**Verdict:** Batch 12A dry-run CLI is available. `--apply` mode (Batch 12B) requires maintainer checklist sign-off and live Sheet column verification via `scripts/verify_sheet_columns.py`.

## Recommended batch sequence (reset)

| Priority | Batch | Scope |
| -------- | ----- | ----- |
| 1 | **10E** | This checkpoint (complete) |
| 2 | **Maintainer** | Close/update #4; sign sheet-import-design checklist; verify Sheet columns |
| 3 | **11A** | Public backend hosting spike (infra only) — optional before import |
| 4 | **10F or doc** | Issue #8 extension wiring design |
| 5 | **11B** | URL validation API (after Issue #5 design) |
| 6 | **12A** | Sheet import CLI (dry-run default) |

Batch 12A should not skip ahead of maintainer approval even though design doc exists.

## Doc vs live MVP drift check

| Doc claim | Live verification |
| --------- | ----------------- |
| Public MVP live at codethor0.github.io/ghost-sweep | Confirmed HTTP 200 |
| Form URL PsjaYrbrCjAgZXjW8 | Confirmed 2x in HTML |
| Full app local Docker only | N/A (not on Pages) |
| Next.js 16.2.9 in README | Not on public MVP (static HTML only) |
| Integrity scoring planned, not public | Live copy matches post-10B softening |

No blocking doc/live drift detected on public surfaces.

## Validation (read-only)

Public MVP validator run at checkpoint: **PASS** (no repo changes).

## Related documents

- [post-launch-roadmap.md](post-launch-roadmap.md)
- [sheet-import-design.md](sheet-import-design.md)
- [moderation-sop.md](moderation-sop.md)
- [implementation-status.md](implementation-status.md)
- [dependency-audit.md](dependency-audit.md)
