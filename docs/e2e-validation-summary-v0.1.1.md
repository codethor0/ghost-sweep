# E2E Validation Summary (v0.1.1)

Date: 2026-07-10  
Environment: Local Docker (`localhost:3000` / `localhost:8000`)  
Scope: Implemented MVP only (auth, report form, read-only dashboards)

## Result

**PASS WITH KNOWN ISSUES**

| Metric | Value |
| ------ | ----- |
| Automated checks (cycle 2/3) | 275 passed, 0 failed, 0 flaky |
| Forms tested (in-app) | 3 / 3 via API + Jest |
| Reports/dashboards tested | 6 / 6 (read-only) |
| Defects found | 3 |
| Defects fixed in v0.1.1 | 3 |

## Fixes in v0.1.1

1. **Live E2E seed discovery** — `scripts/live_e2e_validation.py` sets `PYTHONPATH` when invoking the demo seed subprocess.
2. **Readable form errors** — `frontend/lib/api/client.ts` formats Pydantic validation arrays as field-level messages instead of raw JSON.
3. **Local validation scripts** — Added `scripts/form_validation_e2e.py` (API negative paths) and `scripts/test_live_e2e_seed_discovery.py` (regression).

## Explicit limitations

- Public Google Form was **not submitted** (production intake; no sandbox).
- Moderation, employer claim, and admin **UI not implemented** (API ACL tested only).
- **No export** features exist to test.
- **Playwright not installed** (dependency approval required per AGENTS.md).
- Firefox, WebKit, responsive matrix, and full WCAG audit **not run**.

## Reproduce locally

```bash
docker compose up -d --build
PYTHONPATH=backend DATABASE_URL=postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5432/ghost_sweep ENVIRONMENT=development python3.11 backend/scripts/seed_demo_data.py

python3.11 scripts/live_e2e_validation.py --skip-public-mvp
python3.11 scripts/form_validation_e2e.py
python3.11 scripts/test_live_e2e_seed_discovery.py
python3.11 scripts/validate_public_mvp.py

cd backend && TEST_DATABASE_URL=postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5433/ghost_sweep_test TEST_REDIS_URL=redis://localhost:6379/1 python3.11 -m pytest -q
cd frontend && npm test -- --ci
```

Generated artifacts (JSON logs, screenshots) belong in local `test-results/` and are gitignored.

See [validation-artifacts.md](validation-artifacts.md) and [local-docker-validation.md](local-docker-validation.md).
