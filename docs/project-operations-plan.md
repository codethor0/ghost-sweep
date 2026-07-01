# Project Operations Plan

Planning document for ghost-sweep public operations, project-owned identity, and future nonprofit transition. This is planning only; no operational services are created or configured by this document.

**Current status:** Public repository and GitHub Pages MVP are live. Full application remains local Docker only. Reconcile operational steps with [implementation-status.md](implementation-status.md) before acting on time-sensitive items.

Baseline commit reference: `1fd1b9b` (2026-07-01). Reconcile with [implementation-status.md](implementation-status.md) and [public-launch-checklist.md](public-launch-checklist.md) before go-live.

## Project identity

### Preferred Google account

**Primary recommendation:** `ghostsweep.community@gmail.com`

Rationale:

- Does not imply a for-profit company
- Fits community-driven job integrity mission
- Leaves room for nonprofit or foundation governance later
- Readable and memorable for contributors and reporters

### Fallback account names (in order)

Use only if the primary address is unavailable at registration:

1. `ghostsweep.project@gmail.com`
2. `ghostsweep.opensource@gmail.com`
3. `ghostsweephq@gmail.com`
4. `ghostsweepteam@gmail.com`

### Why project-owned over personal Gmail

| Factor | Project account | Personal Gmail |
| ------ | --------------- | -------------- |
| Ownership transfer | Share or transfer Form, Sheet, Drive to new maintainers | Tied to one individual |
| Open-source credibility | Clear project identity | Informal or personal |
| Collaborator access | Scoped sharing without personal Drive exposure | Risk of mixed personal/project data |
| Future nonprofit / foundation | Natural asset bucket for the project | Requires painful migration |
| Recovery and continuity | Dedicated recovery contacts and password manager entry | Single-person dependency |

All public operational services (Forms, Sheets, Drive folders, future Workspace) should eventually belong to the **project**, not an individual maintainer.

### Reserved target identities (document now; register when ready)

Consistent branding reduces friction if the project grows. Register when available; none are required for MVP.

| Service | Target identity | Status |
| ------- | --------------- | ------ |
| Gmail (operations) | `ghostsweep.community@gmail.com` | Planned |
| GitHub org (future) | `ghost-sweep` | Not created; repo under `codethor0` |
| Domain (future) | `ghostsweep.org` or `ghost-sweep.org` | Not registered |
| Bluesky / X / LinkedIn (future) | `@ghostsweep` or equivalent | Not registered |
| YouTube (future) | `ghostsweep` | Not registered |

## Google services inventory

All services below should be owned by the **project Google account** (`ghostsweep.community@gmail.com` or chosen fallback), not a personal Gmail.

### Google Forms

| Item | Detail |
| ---- | ------ |
| Purpose | Public report intake for the static MVP |
| Owner | Project Google account |
| Spec | [google-form-intake-spec.md](google-form-intake-spec.md) |
| Current repo state | Real Form URL in `public-mvp/index.html` (Batch 8A) |
| Not | Personal Gmail |

### Google Sheets

| Item | Detail |
| ---- | ------ |
| Purpose | Manual moderation queue linked to Form responses |
| Owner | Project Google account |
| Access | Maintainers only; no public link |
| Review columns | `review_status`, `reviewer`, `notes` (manual) |
| Not | Personal Gmail |

### Google Drive

| Item | Detail |
| ---- | ------ |
| Purpose | Project-owned documentation, public assets, moderation records |
| Owner | Project Google account |
| MVP scope | Form-linked Sheet; optional folder for launch assets |
| Not | Personal Gmail |

### Google Calendar (future)

| Item | Detail |
| ---- | ------ |
| Purpose | Community meetings, release planning, maintainer sync |
| Owner | Project Google account |
| MVP | Not required |

### Google Groups (future)

| Item | Detail |
| ---- | ------ |
| Purpose | Maintainers list, moderators list, low-volume announcements |
| Owner | Project Google account |
| MVP | Not required; GitHub Issues suffice for now |

## Google Form rollout plan

### Architecture (MVP)

```text
GitHub Pages (public-mvp/)
        |
        v
Google Form (project account)
        |
        v
Google Sheet (maintainer moderation queue)
        |
        v
Manual moderation
        |
        v
Future backend import (when hosted)
```

### Principles

- Current MVP uses Google Forms; the static site has no backend.
- Future versions may add native backend submission when FastAPI/PostgreSQL is publicly hosted.
- Do **not** remove Google Forms until backend hosting, moderation UI, and import pipeline exist and are validated.
- Form URL replacement in the repo is **Batch 8A** (complete pending commit; real URL `https://forms.gle/PsjaYrbrCjAgZXjW8`).

### Rollout steps (human, outside repo)

1. Create project Google account (preferred: `ghostsweep.community@gmail.com`).
2. Create Form per [google-form-intake-spec.md](google-form-intake-spec.md).
3. Link responses to a new Sheet; restrict sharing to maintainers.
4. Submit one test response; verify all fields in Sheet.
5. Copy public Send link (`https://forms.gle/...`).
6. Run Batch 8A: replace placeholder in `public-mvp/index.html`, update validator, docs, preview locally.
7. Human review of copy and privacy wording.
8. Enable GitHub Pages (`main` / `/public-mvp`) when approved.
9. Make repository public only after checklist complete.

## Future nonprofit and governance readiness

Planning only. No legal or tax implementation in this document.

### Project ownership

- Code: GitHub repository (public at https://github.com/codethor0/ghost-sweep).
- Operations: project Google account owns Form, Sheet, Drive.
- Goal: assets transferable to a nonprofit, foundation, or community org without re-creating intake infrastructure.

### Domain ownership

- Register project domain when budget allows; point to GitHub Pages or future site.
- Domain registrar account should align with project identity, not solely personal email long term.

### Google Workspace upgrade

- Free Gmail suffices for MVP (Form + Sheet + Drive).
- Consider Google Workspace Nonprofits or paid Workspace when multiple maintainers need shared drives, Groups, and audit logs.

### Nonprofit eligibility

- If the project pursues 501(c)(3) or equivalent, Form/Sheet/Drive under project account simplify asset donation and handoff.
- Consult qualified counsel for entity formation; this doc is not legal advice.

### Maintainer transfer process

1. Document current owners in this plan and [public-launch-checklist.md](public-launch-checklist.md).
2. Add new maintainer to GitHub (Write, not Admin unless required).
3. Share Form/Sheet/Drive with new maintainer Google account (Editor on Sheet; not Owner until trusted).
4. Update CODEOWNERS and recovery contacts.
5. Rotate shared credentials via password manager; never commit secrets.

### Shared credentials policy

- No passwords in git, issues, or chat logs.
- Use a password manager (maintainer vault or shared project vault).
- MFA required on project Google account and GitHub org/account.
- Recovery email and phone on project account must be maintained.

### Least privilege

- GitHub: Write for contributors; Admin only for repo owners.
- Google Sheet: Viewer for read-only roles; Editor for moderators; Owner limited to project account holder(s).
- Backend production secrets: not applicable until public hosting.

## Public contributor readiness assessment

Review at baseline `b4018b7`. Batch 6E contributor readiness is **already implemented**; items below note gaps before **public** launch.

### Already present

| Item | Location |
| ---- | -------- |
| Contributor Covenant | `CODE_OF_CONDUCT.md` |
| Contributing guide | `CONTRIBUTING.md` |
| Contributor onboarding | `docs/contributor-onboarding.md` |
| Issue templates | `.github/ISSUE_TEMPLATE/` (contributor task, bug report, docs task) |
| Feature request template | `.github/ISSUE_TEMPLATE/feature_request.md` |
| Pull request template | `.github/pull_request_template.md` |
| CODEOWNERS | `.github/CODEOWNERS` |
| Security disclosure | `SECURITY.md` |
| Moderation model (product) | `docs/moderation-model.md` |
| Legal risk notes | `docs/legal-risk.md` |
| Label taxonomy | `docs/labels.md` |
| Launch checklist | `docs/public-launch-checklist.md` |

### Recommended before public launch (planning only; not created in this batch)

| Item | Gap | Priority |
| ---- | --- | -------- |
| Maintainer guide | No standalone `docs/maintainer-guide.md` (onboarding scattered) | High |
| Governance document | No formal decision-making / escalation doc | Medium |
| Public moderation policy | Product moderation exists; public-facing reporter/moderator policy thin | High |
| Contributor ladder | No explicit path from first PR to maintainer | Low |
| Dedicated security disclosure email | SECURITY.md uses maintainer email; consider project alias later | Medium |

## Launch dependency map

Critical path to public site and contributors (simplified):

```text
Repository PRIVATE
        |
        v
Project Google account created
        |
        v
Google Form published (project account)
        |
        v
Google Sheet linked and restricted
        |
        v
Replace placeholder URL (Batch 8A)
        |
        v
Validator updated (Batch 8A)
        |
        v
Public MVP local preview + Form click-through test
        |
        v
Human review (copy, privacy, disclaimer)
        |
        v
Enable GitHub Pages (manual; main / public-mvp)
        |
        v
Repository PUBLIC (optional ordering; can be before or after Pages test)
        |
        v
Community contributors (Greg and others; Write access already invited)
```

Parallel tracks (not on critical path for static MVP):

- Full backend hosting (deferred)
- Native backend report submission (deferred)
- CI billing history (CI green at `b4018b7`; monitor ongoing)
- Issue #4 closure after Batch 7E acceptance

**Current blockers for public site:** human review, Pages enable, maintainer sign-off. Form URL, project Google account, and Sheet are complete (G1A / 8A).

**Current blockers for public repo:** above plus launch checklist completion.

## Batch history summary

| Batch | Scope | Status |
| ----- | ----- | ------ |
| 6A | (see README / early foundation) | Complete |
| 6B | Backend APIs, auth, scoring | Complete |
| 6C | Frontend wired to backend | Complete |
| 6D | Job URL validation offline helper | Complete |
| 6E | Contributor readiness (templates, CODEOWNERS, labels) | Complete |
| 6F-6I | Docs sync, E2E evidence, dependency triage | Complete |
| 7B-7F | Backend/frontend advisories, Next 16, dev tooling, triage, CI mypy | Complete |

## Recommended next batches

| Batch | Scope | Depends on |
| ----- | ----- | ---------- |
| **8A** | Replace Form URL, validator, docs, preview | Complete (pending commit) |
| **8B** | Commit operations plan + cross-link from launch checklist | Maintainer approval |
| **8C** | Enable GitHub Pages + end-to-end public MVP test | 8A + human review |
| **9A** | Public repo visibility + Issue #2 closure | 8C + checklist |

Batch 6E (public contributor readiness) is **done**; do not re-run. Next operational work is **Batch 8C** (Pages enable after human review).

## Related documents

- [google-form-intake-spec.md](google-form-intake-spec.md)
- [public-launch-checklist.md](public-launch-checklist.md)
- [free-public-launch-plan.md](free-public-launch-plan.md)
- [implementation-status.md](implementation-status.md)
- [contributor-onboarding.md](contributor-onboarding.md)
