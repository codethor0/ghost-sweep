# Audit Remediation Plan

Follow-up work from the independent public audit (Batch 10B). This document tracks remediated items and deferred batches.

## Remediated in Batch 10B

| Finding | Action |
| ------- | ------ |
| Stale docs (Next.js 14, private repo, CI billing-blocked) | Active docs updated; launch plan archived |
| Wrong open issue count (5 vs 6) | Corrected in implementation-status and contributor-onboarding |
| Missing GitHub metadata | Description and homepage set via `gh repo edit` |
| AppleDouble pollution in audit bundles | `create_audit_bundle.py` fail-fast on `._*` and `.DS_Store` |
| Fragile Pages root mirror | Added `scripts/sync_public_mvp.py` |
| Public MVP overclaim and batch jargon | Copy softened; footer links added |
| Weak evidence URL validation | Request validators require http/https; reject dangerous schemes |
| Branch protection undocumented | See [repository-security.md](repository-security.md) |

## Deferred: service test coverage (Batch 10C+)

Do not attempt full coverage remediation in a single docs batch. Prioritized modules and test categories:

| Module | Current gap | Priority test categories |
| ------ | ----------- | ------------------------ |
| `app/services/employer_claims.py` | ~49% | Reject/approve state transitions; duplicate pending claims; auth boundaries; malformed payloads |
| `app/services/reports.py` | ~50% | Invalid job_posting_id; duplicate reports; pagination edge cases; status filter boundaries |
| `app/services/employer_responses.py` | ~57% | Non-employer rejection; disputed vs pending transitions; evidence URL validation at API layer |
| `app/services/moderation.py` | ~57% | verify/dismiss from invalid states; admin-only ACL; audit log side effects |
| `app/services/job_postings.py` | ~68% | Unknown IDs; empty lists; score snapshot consistency |
| `app/services/companies.py` | ~71% | Pagination; unknown company; score breakdown presence |

### Shared test themes

- Negative paths and 4xx responses with stable error bodies
- Auth and authorization boundaries (anonymous, user, employer, admin)
- Duplicate submission and idempotency where applicable
- Malformed input (empty strings, over-length fields, invalid UUIDs)
- Status transition guards (only valid state changes succeed)

Target: raise each listed module to at least 80% without lowering global coverage floor.

## Deferred: Issue #4 dependency advisories

Batch 7E classified remaining advisories as accepted deferred (PostCSS moderate) or local-environment noise (host pip/wheel).

**Recommendation:** Maintainer may close Issue #4 with a comment linking to the Batch 7E section in [dependency-audit.md](dependency-audit.md), or keep open for periodic re-audit. Do not close without explicit maintainer approval.

## Deferred: moderation SOP (Batch 10C)

Sheet column conventions and maintainer triage SOP remain planning work (Issue #7). No code in Batch 10B.

## Related documents

- [repository-security.md](repository-security.md)
- [post-launch-roadmap.md](post-launch-roadmap.md)
- [implementation-status.md](implementation-status.md)
- [dependency-audit.md](dependency-audit.md)
