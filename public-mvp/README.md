# public-mvp

This folder is the free GitHub Pages public MVP for ghost-sweep. It is a standalone static site with no build step, no backend calls, and no secrets.

## What this is

- A static landing and report-intake page for early public visibility
- Report submissions route to a Google Form (placeholder URL until the real form is created)
- Manual review via Google Sheet before any backend import

## What this is not

- The full Next.js frontend in `frontend/` (server-mode; local Docker only)
- The FastAPI backend in `backend/` (local Docker only)
- A live scoring database or authenticated user experience

## Files

| File | Purpose |
| ---- | ------- |
| `index.html` | Landing page with problem statement, status, privacy notes, and CTAs |
| `styles.css` | Responsive layout and accessible contrast |
| `.nojekyll` | Disables Jekyll processing on GitHub Pages |

## Preview locally

From the repository root:

```bash
python3 -m http.server 8080 --directory public-mvp
```

Open http://localhost:8080/ in a browser.

## GitHub Pages configuration

GitHub Pages serves static files only. It cannot run FastAPI, PostgreSQL, or Redis.

Recommended manual setup (no GitHub Actions required):

1. Open repository **Settings** -> **Pages**
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**
3. Select branch **main** and folder **/public-mvp**
4. Save

The site will be available at `https://<username>.github.io/ghost-sweep/` for project Pages.

**Note:** GitHub Actions may be billing-blocked on this account. Branch and folder publishing avoids Actions for Pages deploy. If Actions is unavailable, do not rely on workflow-based Pages deploy until billing is resolved.

## Before going live

1. Create the Google Form per [docs/google-form-intake-spec.md](../docs/google-form-intake-spec.md)
2. Replace `https://forms.gle/REPLACE_WITH_REAL_FORM_URL` in `index.html` with the real Form URL
3. Complete [docs/public-launch-checklist.md](../docs/public-launch-checklist.md)
4. Run validation:

```bash
python3.11 scripts/validate_public_mvp.py
```

## Related documents

- [docs/free-public-launch-plan.md](../docs/free-public-launch-plan.md)
- [docs/google-form-intake-spec.md](../docs/google-form-intake-spec.md)
- [docs/public-launch-checklist.md](../docs/public-launch-checklist.md)
