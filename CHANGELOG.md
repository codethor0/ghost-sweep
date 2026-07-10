# Changelog

All notable changes to Ghost Sweep are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.1] - 2026-07-10

Patch release validating and hardening local E2E workflows discovered during pre-launch QA.

### Fixed

- Live E2E demo posting discovery when `scripts/seed_demo_data.py` is invoked from `scripts/live_e2e_validation.py` (missing `PYTHONPATH`).
- Frontend API client now shows readable field-level validation messages instead of raw JSON for 422 responses.

### Added

- `scripts/form_validation_e2e.py` for local API negative-path checks on auth and report forms.
- `scripts/test_live_e2e_seed_discovery.py` regression check for demo posting discovery.
- `docs/e2e-validation-summary-v0.1.1.md` concise QA summary for the validated local MVP scope.

## [0.1.0] - 2026-07-10

Initial public open-source MVP release. Active development; not production-complete.

### Added

- Public GitHub Pages site at https://codethor0.github.io/ghost-sweep/
- Google Form intake for suspected ghost job reports
- Manual Google Sheet moderation workflow (private; not in repository)
- Offline job URL validation helpers and tests
- Community governance: GOVERNANCE.md, reporting policy, CODEOWNERS, issue templates
- Branch protection on `main` with required CI checks and code owner review
- Community contribution roadmap (Issue #15) and starter issues #11 through #14
- GitHub Discussions for community questions

### Current limitations

- Full backend (FastAPI, PostgreSQL, Redis) runs in local Docker only; not publicly hosted
- No public moderation UI; manual Sheet workflow only
- Production Sheet import automation not enabled
- Sheet import `--apply` not implemented
- Live Gate 11 and Live Gate 12 remain BLOCKED-LIVE
- Reports submitted through the Form are unverified allegations until moderation

### Security

- MIT License preserved
- SECURITY.md documents private vulnerability reporting to codethor@gmail.com

[0.1.1]: https://github.com/codethor0/ghost-sweep/releases/tag/v0.1.1
[0.1.0]: https://github.com/codethor0/ghost-sweep/releases/tag/v0.1.0
