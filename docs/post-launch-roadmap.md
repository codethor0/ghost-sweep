# Post-Launch Product Roadmap

Planning document after static MVP public launch (Batches 9A--9C complete at commit `f1e7ce1`). No backend schema or API changes are implied by this roadmap until separate design approval.

## Launch status (complete)

| Item | Status |
| ---- | ------ |
| Public repository | https://github.com/codethor0/ghost-sweep |
| GitHub Pages static MVP | https://codethor0.github.io/ghost-sweep/ |
| Google Form intake | https://forms.gle/PsjaYrbrCjAgZXjW8 |
| Google Sheet moderation queue | Project account; manual review |
| CI on `main` | Passing |
| Full app hosting | Local Docker only (intentional) |

Architecture today:

```text
GitHub Pages (static MVP) --> Google Form --> Google Sheet --> manual moderation
                                                                    |
                                                                    v
                                              future import --> PostgreSQL backend
```

## Guiding principles

- Static MVP remains the public intake path until hosted backend and moderation UI are validated.
- Do not remove Google Forms until backend intake, moderation tooling, and import pipeline exist and are tested.
- No schema or API changes without maintainer design approval and tests.
- Prefer offline, testable helpers before network integration (see Issue #5).

## Track 1: Google Sheet import planning

**Goal:** Define how approved Form/Sheet rows become backend records without implementing import yet.

**Current state:**

- Sheet columns: Form responses plus manual `review_status`, `reviewer`, `notes`
- Backend expects structured reports tied to `job_posting_id` (see [moderation-model.md](moderation-model.md))
- No automated import script or API exists

**Planning deliverables (Issue #6):**

1. Field mapping: Form/Sheet columns to future backend entities (company, posting, report narrative)
2. Duplicate detection strategy (URL normalization via [job_url_validation.py](../backend/app/services/job_url_validation.py))
3. Moderation gates: which `review_status` values may import
4. Idempotency and audit requirements
5. PII redaction rules before any public display
6. Explicit non-goals for v1 (no scraping, no auto-verify)

**Dependencies:** Manual moderation SOP (Track 2), URL validation rules (Issue #5)

## Track 2: Moderation workflow

**Goal:** Document and stabilize manual moderation for Form/Sheet intake; plan product moderation UI later.

**Current state:**

- All public reports enter via Google Form
- Maintainers review in linked Sheet only
- Backend moderation APIs exist for in-app reports but are not wired to Form intake

**Near-term (operational, no code required):**

1. Sheet review SOP: triage, duplicate check, approve/reject values for `review_status`
2. Response SLAs and escalation (see [moderation-model.md](moderation-model.md))
3. Redaction checklist before any public summary

**Product milestones (Issue #7, future batches):**

1. Moderation queue UI in frontend (admin)
2. Bridge Sheet-approved rows to backend (Track 1)
3. Evidence upload when policy allows (deferred)

## Track 3: Extension API wiring plan

**Goal:** Plan how the MV3 extension hands off job URLs to backend/frontend when API is available.

**Current state:**

- Extension opens local frontend with `?posting_url=` query param only
- No backend API calls from extension
- Offline URL validation helper exists (Batch 6D); API wiring deferred (Issue #5)

**Planning deliverables (Issue #8):**

1. Target UX: popup shows normalized URL, provider hint, link to public Form vs in-app report (when hosted)
2. Configuration: public API base URL vs local dev
3. Auth model for extension (likely none for read-only lookup; defer write paths)
4. Manifest permissions review before any network calls
5. Test strategy (unit + manual; no live scraping in CI)

**Dependencies:** Public backend hosting decision, Issue #5 design, Track 1 import policy

## Track 4: Contributor lanes (good first issues)

**Completed foundation:** Issue #1 initial scope shipped in Batch 6D (`job_url_validation.py` + tests).

**Recommended good-first lanes (no schema/API):**

| Lane | Area | Scope |
| ---- | ---- | ----- |
| Expand URL validation tests | `area:backend`, `good first issue` | More ATS/career URL fixtures; edge cases |
| Docs gaps | `area:docs`, `good first issue` | Moderation SOP, import mapping drafts |
| Static MVP accessibility | `area:public-mvp` | HTML/CSS a11y improvements; mirror to root |
| Validator hardening | `area:tests` | Additional public-mvp validator checks |

**Not good first issues:** Sheet import implementation, extension network calls, schema migrations, auth changes.

## Track 5: Issue tracker hygiene

| Issue | Action |
| ----- | ------ |
| #2 Form/Pages launch | Close -- completed in 9A--9C |
| #3 CI billing | Close or update -- CI passing on `main` at `f1e7ce1` |
| #4 Dependency advisories | Narrow -- Batch 7E accepted deferred; maintainer may close |
| #1 URL validation onboarding | Refocus -- 6D foundation done; extend tests/docs |
| #5 URL validation API design | Keep open -- design gate before API wiring |
| #6 Sheet import planning | New -- design only |
| #7 Moderation workflow | New -- SOP + product plan |
| #8 Extension API wiring plan | New -- design only |

## Recommended batch sequence

| Batch | Scope | Schema/API |
| ----- | ----- | ---------- |
| **10A** | Roadmap + issue tracker sync (this doc) | No |
| **10B** | Moderation SOP doc + Sheet column conventions | No |
| **10C** | Sheet import design doc (field mapping) | No |
| **11A** | Public backend hosting spike (infra only) | No schema change |
| **11B** | URL validation API wiring (after Issue #5 approval) | API only if approved |
| **12A** | Sheet import script (after 10C approval) | May require schema approval |

## Related documents

- [public-launch-checklist.md](public-launch-checklist.md)
- [implementation-status.md](implementation-status.md)
- [free-public-launch-plan.md](free-public-launch-plan.md)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [moderation-model.md](moderation-model.md)
- [contributor-onboarding.md](contributor-onboarding.md)
