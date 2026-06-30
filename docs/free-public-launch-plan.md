# Free Public Launch Plan

This document defines a practical zero-cost path to make ghost-sweep publicly visible before paid backend hosting is justified. It does not claim the full-stack product is production-ready.

## Current baseline

| Layer | Status |
| ----- | ------ |
| Backend (Batch 6B) | Works locally via Docker Compose (FastAPI, PostgreSQL, Redis) |
| Frontend (Batch 6C) | Wired to backend APIs for local development |
| Job URL validation (Batch 6D) | Offline foundation complete; not API-wired |
| Extension | MV3 scaffold only; no backend API integration |
| Public MVP | Static files in `public-mvp/`; not live; Form URL placeholder |
| Public hosting | Not deployed; GitHub Pages not enabled |
| Repository | Private |
| CI | GitHub Actions blocked by billing/spending limits before job steps run |
| Latest baseline | `6074691` (Batch 6E contributor readiness; Batch 6F docs sync) |
| Contributor readiness | Batch 6E complete: labels, templates, CODEOWNERS, Issue #1 |
| Tracking issues | #2 Form/Pages launch, #3 CI billing, #4 dependency advisories, #5 URL validation API design |

The full database-backed application remains a local development stack. Public launch uses static hosting plus manual intake until traction justifies paid infrastructure.

---

## Option A: GitHub Pages + Google Forms (recommended MVP)

### Architecture

```text
User browser
    |
    v
GitHub Pages (static HTML/CSS/JS from repo)
    |
    +-- Home: problem statement, disclaimer, links
    |
    +-- Report CTA --> Google Form (external)
                              |
                              v
                        Google Sheet (maintainer inbox)
                              |
                              v
                        Manual review and moderation
                              |
                              v
                        Future import into PostgreSQL backend
```

### Flow

1. Static frontend is built and published to GitHub Pages from the repository.
2. The home page explains ghost jobs, the community report concept, and project status.
3. A prominent "Submit a report" button opens a Google Form in a new tab.
4. Google Form responses are linked to a Google Sheet (Google's native integration).
5. Maintainers review submissions manually, redact sensitive fields, and decide what to publish.
6. Approved records can later be imported into the backend when hosted.

### Google Form fields (MVP intake)

| Field | Required | Notes |
| ----- | -------- | ----- |
| Job URL | Yes | Primary identifier for the posting |
| Company name | Yes | As shown on the job board or employer site |
| Job title | Yes | |
| Location / remote | Yes | City, region, or "Remote" |
| Date seen | Yes | When the user observed the posting |
| Why suspected ghost job | Yes | Free text; minimum length guidance in form description |
| Evidence links | No | URLs to repost history, screenshots hosted elsewhere, etc. |
| Wants follow-up | Yes | Yes / No |
| Email (optional) | No | Only if user wants follow-up; never published raw |
| Consent | Yes | Checkbox: "I confirm this submission is good-faith and accurate to my knowledge" |

### Privacy and moderation

- Do not ask for government IDs, home addresses, phone numbers, or employer HR contact details.
- Do not publish raw email addresses in any public view.
- Form description must state: submissions are reviewed manually; publication is not guaranteed; false or abusive reports may be discarded.
- Maintainers redact identifying personal information before any public summary.
- Evidence file upload remains deferred; link-only evidence for MVP.

### Pros

- Free (GitHub Pages + Google Forms/Sheets free tier)
- Fast to launch; no backend hosting or database operations
- No secrets in the static site beyond a public Form URL
- Familiar intake workflow for early community reports

### Cons

- No live scoring database or search on the public site
- Manual moderation; no automated duplicate detection
- No authenticated user accounts on the public MVP
- Google Form dependency (third-party ToS and data residency)
- Import into backend is a separate manual or scripted step

---

## Option B: GitHub Pages + GitHub Issues

### Architecture

```text
User browser
    |
    v
GitHub Pages (static frontend)
    |
    +-- Report CTA --> GitHub Issue (prefilled template)
                              |
                              v
                        Public issue thread + labels
                              |
                              v
                        Maintainer moderation via labels/lock/close
```

### Flow

1. Static frontend links to a GitHub Issue template with prefilled title/body fields.
2. Community members can comment and discuss suspected ghost jobs publicly.
3. Maintainers apply labels (e.g. `report-intake`, `needs-review`, `verified`, `duplicate`, `spam`).
4. Closed or locked issues act as moderation outcomes.

### Pros

- Transparent and open-source native
- No third-party form provider
- Discussion and community visibility built in
- Version-controlled issue templates in the repo

### Cons

- Public by default; reporters may not want visibility
- Privacy concerns for optional contact info even in issue bodies
- Moderation burden scales with volume
- Issue noise can overwhelm maintainers
- Harder to structure fields than a form (parsing free-form issue bodies)

---

## Option C: Full-stack local app (development only)

### Architecture

```text
Developer machine or private network
    |
    v
Docker Compose
    +-- FastAPI backend (:8000)
    +-- PostgreSQL 15
    +-- Redis 7
    +-- Next.js frontend (:3000)
```

### Status

- Batch 6B backend and Batch 6C frontend are implemented and validated locally.
- This stack is **not** hosted publicly yet.
- Suitable for continued development, contributor onboarding with Docker, and integration testing.

### Future hosting path (when traction exists)

Paid or free-tier managed services to evaluate later (requires approval before implementation):

- Render, Fly.io, Railway for backend containers
- Supabase or Neon for managed PostgreSQL
- Upstash for managed Redis
- Vercel or Cloudflare Pages for SSR/ISR frontend (if static export is insufficient)

No paid hosting should be started until intake volume or contributor activity justifies it.

---

## Recommendation

| Purpose | Path |
| ------- | ---- |
| Public MVP intake and awareness | **Option A** (GitHub Pages + Google Forms) via `public-mvp/` |
| Continued backend/frontend development | **Option C** (local Docker stack) |
| Optional parallel transparency channel | Option B as a secondary link, not primary intake |

Option A minimizes cost, privacy exposure, and operational load while the database-backed product matures locally.

**Implemented approach:** Standalone static site in `public-mvp/` (plain HTML/CSS). The full Next.js app is not converted to static export in this batch.

---

## Public MVP UX plan

### Home page (static)

Content blocks:

1. **Hero**: Explain ghost jobs and why hiring transparency matters.
2. **How it works**: Community reports, manual review, future scoring database.
3. **Primary CTA**: "Submit a report" linking to the Google Form URL.
4. **Secondary links**: GitHub repository, CONTRIBUTING.md, issue tracker.
5. **Disclaimer banner** (always visible):

   > Early public MVP. Report submissions are reviewed manually. This site does not yet connect to a live scoring database. The full application runs locally for development only.

6. **Deferred features notice**: Evidence upload, browser extension API integration, and public backend API are not available on this site.

Remove or hide from public MVP (until backend is hosted):

- Login / register / dashboard (require live API)
- Live companies and postings browse (require live API and data)
- API health panel pointing at localhost

### Report page (static MVP)

For the GitHub Pages deployment, replace the authenticated in-app report form with:

- Explanation of what makes a useful report
- Link to Google Form with the fields listed above
- Privacy and moderation disclaimer
- Note that the in-app report form (`POST /api/v1/reports`) is available only in local development

### Navigation (public MVP)

| Link | Target |
| ---- | ------ |
| Home | `/` |
| Submit report | Google Form (external) |
| GitHub repo | `https://github.com/codethor0/ghost-sweep` |
| Contribute | `/CONTRIBUTING.md` on GitHub |
| Security | `/SECURITY.md` on GitHub |

---

## GitHub Pages deployment requirements

GitHub Pages serves static files only. It does not run FastAPI, PostgreSQL, or Redis.

**Deploy source:** `public-mvp/` folder on branch `main`.

Manual setup (preferred when GitHub Actions is billing-blocked):

1. Settings -> Pages -> Deploy from a branch -> main -> /public-mvp
2. Replace Google Form placeholder URL in `public-mvp/index.html` before going live
3. Run `python3.11 scripts/validate_public_mvp.py`

Publishing via GitHub Actions may remain blocked by account billing limits. Branch and folder publishing avoids Actions for Pages deploy.

See [public-mvp/README.md](../public-mvp/README.md) and [public-launch-checklist.md](public-launch-checklist.md).

---

## GitHub Pages feasibility (current frontend)

The Batch 6C Next.js frontend **cannot** be statically exported to GitHub Pages without code changes.

### Blockers

| Issue | Detail |
| ----- | ------ |
| No static export config | `frontend/next.config.mjs` has no `output: 'export'` |
| Server Components with build-time fetch | `/companies`, `/companies/[id]`, `/postings/[id]` are async Server Components calling the API at render time |
| Dynamic routes | `[id]` segments require `generateStaticParams` or client-side routing for static export |
| Dynamic searchParams | Home (`posting_url`) and companies (`page`) use `searchParams`, which prevents static generation |
| API base URL | Server-side fetch resolves to `http://backend:8000` or `localhost:8000`; unavailable on GitHub Pages |
| Project Pages base path | GitHub project sites serve from `/ghost-sweep/`; requires `basePath` and `assetPrefix` |

### Proposed minimal changes (approval required before implementation)

1. Add a `pages-mvp` or `static-export` build profile with `output: 'export'`, `basePath: '/ghost-sweep'`, and `trailingSlash: true`.
2. Split or gate routes: public MVP includes only `/` and `/report` (static); hide auth, dashboard, and API-dependent browse pages from the export.
3. Convert MVP pages to static content or client components that degrade gracefully when no API is configured.
4. Add a GitHub Actions workflow for Pages deploy (requires CI/CD approval).
5. Set `NEXT_PUBLIC_API_BASE_URL` empty or unset for the Pages build so health checks show "API unavailable" instead of failing the build.

Alternative with fewer Next.js changes: publish a minimal standalone `public-mvp/` directory (plain HTML/CSS) for GitHub Pages and keep the full Next.js app for local Docker only.

**Status:** `public-mvp/` implemented. Full Next.js static export not required for public MVP.

---

## Pre-public repository checklist

Before making the repository public:

- [ ] Commit or discard pending local changes (docs, tests, seed script)
- [ ] Ensure no secrets, tokens, or `.env` files are tracked
- [ ] Redact or delete local validation logs (see [validation-artifacts.md](validation-artifacts.md))
- [ ] Resolve GitHub Actions billing or document manual verification as source of truth
- [ ] Update README, CONTRIBUTING, SECURITY, and implementation-status with public MVP disclaimers
- [ ] Create Google Form and link it in the static MVP
- [x] Implement standalone `public-mvp/` static site
- [ ] Replace Google Form placeholder URL in `public-mvp/index.html`
- [ ] Enable GitHub Pages on the repository (Settings -> Pages -> /public-mvp)

---

## Deferred until post-MVP

- Evidence file upload
- Browser extension backend API integration (deferred; offline URL validation foundation exists from Batch 6D but is not API-wired)
- Public backend API hosting
- Live integrity scores and company browse on the public site
- Frontend moderation, employer, and admin UI
- Refresh token persistence in the frontend
- Automated import from Google Sheets to PostgreSQL
- Dependency advisory remediation (see [dependency-audit.md](dependency-audit.md))

---

## Related documents

- [README.md](../README.md) -- project overview and local setup
- [implementation-status.md](implementation-status.md) -- Batch 6B/6C scope
- [local-docker-validation.md](local-docker-validation.md) -- Docker validation checkpoint
- [dependency-audit.md](dependency-audit.md) -- known advisories
- [validation-artifacts.md](validation-artifacts.md) -- redaction rules for logs
- [google-form-intake-spec.md](google-form-intake-spec.md) -- Google Form field spec
- [public-launch-checklist.md](public-launch-checklist.md) -- pre-public checklist
- [public-mvp/README.md](../public-mvp/README.md) -- static site deploy guide
