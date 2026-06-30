## Summary

<!-- What does this pull request do and why? -->

## Scope

<!-- Keep the change small and intentional. List what is in scope and out of scope. -->

## Related issue

<!-- Link the issue this PR addresses, e.g. Fixes #1 -->

## Changed files

<!-- List primary files touched. -->

## Verification run

<!-- Paste commands and results. Local verification is source of truth while CI billing is blocked. -->

```bash
# Example backend
cd backend && pytest -v --cov=app --cov-fail-under=80

# Example frontend
cd frontend && npm run lint && npm run typecheck && npm test
```

## Screenshots (if UI)

<!-- Required for visible frontend or public-mvp changes. -->

## Risk checklist

- [ ] Tests pass locally
- [ ] Lint and type checks pass locally
- [ ] Documentation updated when behavior or contributor workflow changed
- [ ] **No backend API, auth, or schema changes** (or separately approved and called out below)
- [ ] **No Docker or CI workflow changes** (or separately approved and called out below)
- [ ] **No secrets or generated artifacts committed** (`.env`, `__pycache__`, `.pyc`, `node_modules`, `.next`, caches, validation logs with tokens)
- [ ] Security and privacy impact considered
- [ ] Rollback plan described for non-trivial changes

## Approval notes

<!-- If this PR touches API, auth, schema, Docker, CI, dependencies, extension integration, or public launch, stop and get maintainer approval first. -->
