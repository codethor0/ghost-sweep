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

## Secure development expectations

- No hardcoded secrets
- No stack traces exposed to end users
- Refresh tokens must remain in HttpOnly cookies
- Access tokens must not be stored in browser localStorage
- Auth endpoints are rate limited
- Dependencies are audited in CI

## Disclosure policy

We aim to coordinate disclosure after a fix or mitigation is available.
