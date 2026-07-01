## Summary

<!-- What does this pull request do and why? -->

## Scope

<!-- Keep the change small and intentional. List what is in scope. -->

## Out-of-scope areas

<!-- Explicitly list paths or systems you did not touch. -->

## Related issue

<!-- Link the issue this PR addresses, e.g. Fixes #1 -->

## Changed files

<!-- List primary files touched. -->

## Verification run

<!-- Paste commands and results. Run local gates before requesting review; CI on main should also pass. -->

```bash
# Example backend
cd backend && pytest -v --cov=app --cov-fail-under=80

# Example frontend
cd frontend && npm run lint && npm run typecheck && npm test
```

## Screenshots (if UI or public-mvp changed)

<!-- Required for visible frontend or public-mvp changes. -->

## Risk level

<!-- Low / Medium / High and why. -->

## Risk checklist

- [ ] Tests pass locally
- [ ] Lint and type checks pass locally
- [ ] Documentation updated when behavior or contributor workflow changed
- [ ] **No backend API, auth, or schema changes** (or separately approved and called out below)
- [ ] **No Docker or CI workflow changes** (or separately approved and called out below)
- [ ] **No secrets or generated artifacts committed** (`.env`, `__pycache__`, `.pyc`, `node_modules`, `.next`, caches, validation logs with tokens)
- [ ] **No tool attribution** in commits, code, comments, or documentation
- [ ] Security and privacy impact considered
- [ ] Rollback plan described for non-trivial changes
- [ ] Draft PR opened early when scope was uncertain

## Approval notes

<!-- If this PR touches API, auth, schema, Docker, CI, dependencies, extension integration, or public launch, stop and get maintainer approval first. -->
