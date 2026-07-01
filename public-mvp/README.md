# public-mvp

This folder is the **canonical source** for the ghost-sweep public MVP static site. It is a standalone site with no build step, no backend calls, and no secrets.

GitHub Pages branch deploy supports **`/` (root) or `/docs` only** — not arbitrary folders. For publishing, root `index.html`, `styles.css`, and `.nojekyll` mirror this folder. Edit files here first, then sync to the repository root.

```bash
python3.11 scripts/sync_public_mvp.py
python3.11 scripts/validate_public_mvp.py
```

## What this is

- A static landing and report-intake page for early public visibility
- Report submissions route to a Google Form at `https://forms.gle/PsjaYrbrCjAgZXjW8`
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

Branch deploy source folders are limited to **`/` (root) or `/docs`**. This project publishes from **root**, with files copied from `public-mvp/`.

Setup:

1. Open repository **Settings** -> **Pages**
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**
3. Select branch **main** and folder **`/` (root)**
4. Ensure root has `index.html`, `styles.css`, and `.nojekyll` (mirrors of this folder)
5. Save

Live site: https://codethor0.github.io/ghost-sweep/

When changing MVP content:

```bash
python3.11 scripts/sync_public_mvp.py
python3.11 scripts/validate_public_mvp.py
```

## Launch status

Public MVP is **live** at https://codethor0.github.io/ghost-sweep/

- Google Form and linked Sheet on project account (G1A)
- Real Form URL in `index.html` (8A)
- GitHub Pages from repo root mirror (9B)
- Full application remains local Docker only

Before editing the live site, run validation:

```bash
python3.11 scripts/validate_public_mvp.py
```

## Related documents

- [docs/post-launch-roadmap.md](../docs/post-launch-roadmap.md)
- [docs/google-form-intake-spec.md](../docs/google-form-intake-spec.md)
- [docs/public-launch-checklist.md](../docs/public-launch-checklist.md)
