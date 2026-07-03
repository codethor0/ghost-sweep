# Post-Launch Product Roadmap

Planning document after static MVP public launch (Batches 9A--9C complete at commit `f1e7ce1`). Current baseline: `ae6897f` (Batch 14C; 14D pending push). No backend schema or API changes are implied by this roadmap until separate design approval.

## Batch 12 closure (MVP readiness)

Batch 12 is **closed for MVP readiness** under amended Section 18 offline gate language (Batch 12S, pushed Batch 12T).

| Milestone | Status |
| --------- | ------ |
| 12A dry-run CLI | Shipped |
| 12B apply-mode design | Shipped |
| 12F-P offline verification | PASS — ACCEPTED-MVP |
| 12Q offline documentation | Complete |
| 12S Section 18 MVP amendment | Complete |
| 12T push checkpoint | Complete |
| Live Sheet export proof | **BLOCKED-LIVE** — deferred; not an MVP blocker under amended gate |
| `--apply` implementation | **Blocked** — separate maintainer decision required |
| Production import automation | **Not enabled** |

See [implementation-status.md](implementation-status.md) Batch 12S and [sheet-import-apply-design.md](sheet-import-apply-design.md) section 18.

## Launch status (complete)

| Item | Status |
| ---- | ------ |
| Public repository | https://github.com/codethor0/ghost-sweep |
| GitHub Pages static MVP | https://codethor0.github.io/ghost-sweep/ |
| Google Form intake | https://forms.gle/PsjaYrbrCjAgZXjW8 |
| Google Sheet moderation queue | Project account; manual review |
| CI on `main` | Passing (run `28672126699` on `ae6897f`) |
| GitHub Pages deploy | Green on `ae6897f` |
| PR #9 (URL validation tests) | Merged |
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

## Track 1: Google Sheet import

**Goal:** Move approved Form/Sheet rows into backend records when maintainer-approved apply mode and hosting exist.

**Current state:**

- Sheet columns: Form responses plus maintainer columns per [moderation-sop.md](moderation-sop.md)
- Batch 12A dry-run CLI shipped — no database writes
- Batch 12B apply-mode design shipped — implementation blocked
- Batch 12F-P offline artifact verification **ACCEPTED-MVP** (Batch 12S)
- Live Google Sheet export proof **BLOCKED-LIVE** — operational blocker; deferred
- `--apply` not implemented; production import automation not enabled

**Completed planning (Issue #6 — Batch 10D):**

1. Field mapping: [sheet-import-design.md](sheet-import-design.md)
2. Duplicate detection strategy using normalized job URLs
3. Import eligibility rules tied to `review_status` and `import_ready`
4. Idempotency and audit requirements
5. PII redaction rules before public use
6. Explicit v1 non-goals (no scraping, no auto-verify)

Apply-mode design: [sheet-import-apply-design.md](sheet-import-apply-design.md). **Do not implement `--apply`** until explicitly approved; live export proof required before production automation.

**Note:** [sheet-import-design.md](sheet-import-design.md) phase table uses **13A = Hosted import** (production DB). That is a future import-automation phase, not the same as Batch 13A/13B/13C roadmap numbering in this document.

**Dependencies:** Manual moderation SOP (Track 2), URL validation rules (Issue #5), hosted backend (Batch 13C)

## Track 2: Moderation workflow

**Goal:** Document and stabilize manual moderation for Form/Sheet intake; plan product moderation UI later.

**Current state:**

- All public reports enter via Google Form
- Maintainers review in linked Sheet only
- Backend moderation APIs exist for in-app reports but are not wired to Form intake

**Near-term (operational, Batch 10C complete):**

1. Sheet review SOP: [moderation-sop.md](moderation-sop.md) — triage, review states, decline codes, import-readiness
2. Response SLAs and escalation documented in SOP
3. Redaction and email privacy rules documented in SOP

**Product milestones (Issue #7):**

1. Moderation UI scope document — **complete** (Batch 13E, [moderation-ui-scope.md](moderation-ui-scope.md))
2. Moderation API contract review — **complete** (Batch 14B, [moderation-api-contract-review.md](moderation-api-contract-review.md))
3. Moderation UI wireframe spec — **complete** (Batch 14C, [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md))
4. Moderation schema decision record — **complete** (Batch 14D, [moderation-schema-decision-record.md](moderation-schema-decision-record.md))
5. Moderation queue UI in frontend (admin) — **deferred**; implementation not started
6. Bridge Sheet-approved rows to backend (Track 1)
7. Evidence upload when policy allows (deferred)

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
| #6 Sheet import | 12A–12S complete for MVP offline gate; `--apply` and live proof **deferred** |
| #7 Moderation workflow | SOP complete (10C); UI scoped (13E); implementation deferred |
| #8 Extension API wiring plan | New -- design only |

## Recommended batch sequence

### Completed (through Batch 12)

| Batch | Scope | Schema/API |
| ----- | ----- | ---------- |
| **10A** | Roadmap + issue tracker sync | No |
| **10B** | Public audit remediation | Request validation only |
| **10C** | Moderation SOP ([moderation-sop.md](moderation-sop.md)) | No |
| **10D** | Sheet import design ([sheet-import-design.md](sheet-import-design.md)) | No |
| **10E** | Implementation readiness checkpoint | No |
| **12A** | Sheet import dry-run CLI | No |
| **12B** | Sheet import apply-mode design gate | No |
| **12C** | Audit remediation and gate cleanup | No |
| **12F-P / 12Q** | Offline artifact verification + documentation | No |
| **12S / 12T** | Section 18 MVP amendment + push | No |

### Post–Batch-12 queue (current)

| Priority | Batch | Scope | Schema/API |
| -------- | ----- | ----- | ---------- |
| 1 | **13B** | Planning doc realignment | No — complete |
| 2 | **13C** | Public backend hosting spike ([hosting-readiness-spike.md](hosting-readiness-spike.md)) | No — complete |
| 3 | **13D** | Render deployment plan ([render-deployment-plan.md](render-deployment-plan.md)) | No — complete |
| 4 | **13E** | Moderation UI scoping ([moderation-ui-scope.md](moderation-ui-scope.md)) | No — complete |
| 5 | **13F–13I** | GitHub health, PR #9 merge, Pages rerun | No — complete |
| 6 | **14B** | Moderation API contract review ([moderation-api-contract-review.md](moderation-api-contract-review.md)) | No — complete |
| 7 | **14C** | Moderation UI wireframe spec ([moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md)) | No — complete |
| 8 | **14D** | Moderation schema decision record ([moderation-schema-decision-record.md](moderation-schema-decision-record.md)) | No — complete |
| 9 | **14E** | Moderation API implementation plan (docs-only) | No |
| 10 | **14F** | Moderation frontend implementation plan (docs-only) | No |
| 11 | **14G** | Moderation migration plan (docs-only) | No |
| 12 | **14A** | Render staging implementation (requires maintainer approval; not authorized by 13D) | Deploy config |
| 13 | **11B** | URL validation API wiring (after Issue #5 approval) | API only if approved |
| — | **doc** | Extension API wiring design (Issue #8) | No |
| — | **Maintainer** | Close/reframe Issue #4; repository security settings | No |
| — | **Deferred** | Live Sheet export proof; `--apply` implementation; hosted production import | Separate decisions |

Live Sheet proof and `--apply` are **deferred gates**, not the next MVP blocker. MVP readiness proceeds under amended Section 18 offline gate language only.

### Historical reference (pre–Batch-12 plan)

| Batch | Scope | Schema/API |
| ----- | ----- | ---------- |
| **11A** | Public backend hosting spike — **renumbered to Batch 13C** in post-12 queue | No schema change |
| **12B impl** | Sheet import `--apply` | **Deferred** — blocked |

## Related documents

- [public-launch-checklist.md](public-launch-checklist.md)
- [implementation-status.md](implementation-status.md)
- [archive/free-public-launch-plan.md](archive/free-public-launch-plan.md) (historical)
- [google-form-intake-spec.md](google-form-intake-spec.md)
- [implementation-readiness-report.md](implementation-readiness-report.md)
- [sheet-import-design.md](sheet-import-design.md)
- [sheet-import-apply-design.md](sheet-import-apply-design.md)
- [moderation-sop.md](moderation-sop.md)
- [moderation-model.md](moderation-model.md)
- [contributor-onboarding.md](contributor-onboarding.md)
- [hosting-readiness-spike.md](hosting-readiness-spike.md)
- [render-deployment-plan.md](render-deployment-plan.md)
- [moderation-ui-scope.md](moderation-ui-scope.md)
- [moderation-api-contract-review.md](moderation-api-contract-review.md)
- [moderation-ui-wireframe-spec.md](moderation-ui-wireframe-spec.md)
