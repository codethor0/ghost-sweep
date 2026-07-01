# Repository Security

Read-only snapshot of GitHub branch protection and ruleset status. Updated during Batch 10B audit remediation.

## Branch protection (`main`)

Captured via GitHub API:

```bash
gh api /repos/codethor0/ghost-sweep/branches/main/protection
```

**Status at Batch 10B:** Branch not protected (HTTP 404 — no classic branch protection rules configured).

## Repository rulesets

```bash
gh api /repos/codethor0/ghost-sweep/rulesets
```

**Status at Batch 10B:** No rulesets configured (empty array).

## Recommendations (maintainer approval required)

Before scaling contributor access or enabling direct pushes from multiple maintainers:

1. **Require pull request reviews** before merge to `main` (at least one approval).
2. **Require status checks** — CI workflow must pass (backend, frontend, extension smoke, public-mvp validator).
3. **Disable force pushes** to `main`.
4. **Restrict who can push** to `main` (maintainers only; contributors via PR).
5. **Enable signed commits** as a soft requirement (already preferred in CONTRIBUTING.md).

These changes require repository admin settings or `gh api` / UI configuration. Batch 10B does not modify branch protection.

## Related documents

- [SECURITY.md](../SECURITY.md)
- [audit-remediation-plan.md](audit-remediation-plan.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
