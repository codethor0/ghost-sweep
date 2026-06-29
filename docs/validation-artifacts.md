# Validation Artifacts Policy

This policy applies to local validation logs, review bundles in Downloads, and any externally shared checkpoint artifacts.

## Required redactions

- Access tokens and refresh tokens must be replaced with `[REDACTED]` or omitted entirely.
- JWT bearer values must never appear in plaintext in review bundles or public reports.
- Production or staging secrets must never be copied into validation artifacts.

## Allowed content

- SQL bootstrap commands used for local validation (INSERT/UPDATE for demo companies, postings, admin flags).
- Local test emails and usernames (for example `e2e_*@example.com`).
- HTTP status codes, endpoint paths, and non-sensitive response fields (IDs, status enums).
- Coverage percentages and test counts.

## Bundle hygiene

Review bundles must exclude:

- `.git`, `.githooks`, `.env`, and `.env.*` except `.env.example` in source snapshots when explicitly included
- `node_modules`, `.next`, caches, coverage output, binaries
- Prompt transcripts and tool attribution strings

## Verification logs

When capturing live validation output:

```bash
export NO_COLOR=1
export FORCE_COLOR=0
export TERM=dumb
```

Redact token lines before writing `VERIFICATION_RAW_LOG_REDACTED.txt` for external review.

See [local-docker-validation.md](local-docker-validation.md) for live validation steps and [SECURITY.md](../SECURITY.md) for sensitive data handling.
