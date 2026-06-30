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
- AppleDouble metadata files (`._*`) and `.DS_Store`
- Prompt transcripts and tool attribution strings

Use `scripts/create_audit_bundle.py` to build clean bundles with strict exclusions and real evidence reports. Do not ship placeholder reports that say "See e2e bundle."

## Correct E2E API expectations

When capturing live validation evidence, use the exact live API contract:

| Step | Method | Path | Expected status | Payload notes |
| ---- | ------ | ---- | --------------- | ------------- |
| Register | POST | `/api/v1/auth/register` | 200 | `email`, `username`, `password` |
| Login | POST | `/api/v1/auth/login` | 200 | `identifier`, `password` |
| Create report | POST | `/api/v1/reports` | **201** | `job_posting_id`, `report_type`, `description` (min 20 chars) |
| Get report | GET | `/api/v1/reports/{report_id}` | **200** | public read |
| Vote | POST | `/api/v1/reports/{report_id}/votes` | **201** | `vote`: `"up"` or `"down"` |
| Job posting | GET | `/api/v1/job-postings/{id}` | 200 | not `/api/v1/postings/` |

Run `python3.11 scripts/live_e2e_validation.py` against a live Docker stack and treat nonzero exit as failure. Do not claim report/vote success unless raw logs show the expected status codes.

## Verification logs

When capturing live validation output:

```bash
export NO_COLOR=1
export FORCE_COLOR=0
export TERM=dumb
```

Redact token lines before writing `VERIFICATION_RAW_LOG_REDACTED.txt` for external review.

See [local-docker-validation.md](local-docker-validation.md) for live validation steps and [SECURITY.md](../SECURITY.md) for sensitive data handling.
