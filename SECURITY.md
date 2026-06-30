# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a vulnerability

Do not open public issues for security vulnerabilities.

Email codethor@gmail.com with:

- Description of the issue
- Steps to reproduce
- Impact assessment
- Suggested remediation if available

You should receive an initial response within 72 hours.

## Sensitive data handling

ghost-sweep processes job posting URLs, employer names, report narratives, and user account data. Do not include live user data, secrets, or production credentials in reports or pull requests.

## Public MVP and Google Form intake

The static public site in `public-mvp/` has no backend, no secrets, and no analytics. Report intake uses Google Forms (temporary). Form responses are stored in a maintainer-only Google Sheet.

- Do not submit credentials or confidential documents through the Form.
- Optional contact email is for follow-up only. Raw emails must not be published.
- Submissions may be moderated before public use. Public data may be anonymized or summarized.
- Google Form data is outside the repository and subject to Google's terms of service.

See [docs/google-form-intake-spec.md](docs/google-form-intake-spec.md).

## Secure development expectations

- No hardcoded secrets
- No stack traces exposed to end users
- Refresh tokens are delivered in JSON response bodies today; only SHA-256 hashes are stored in Redis
- HttpOnly cookie transport for refresh tokens is deferred future work
- Access tokens must not be stored in browser localStorage
- Docker Compose defaults in `.env.example` are development-only placeholders, not production values
- Auth endpoints are rate limited
- Dependencies are audited locally and in CI when billing permits; see [docs/dependency-audit.md](docs/dependency-audit.md) for known deferred advisories (Issue #4)
- External validation bundles and review artifacts must redact access and refresh tokens; see [docs/validation-artifacts.md](docs/validation-artifacts.md)

## Disclosure policy

We aim to coordinate disclosure after a fix or mitigation is available.
