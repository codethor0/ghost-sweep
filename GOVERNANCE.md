# Governance

This document describes how ghost-sweep is maintained as a volunteer open-source project.

## Project owner

**GitHub:** [@codethor0](https://github.com/codethor0)

**Responsibilities:**

- Project direction and release policy
- Privacy and data-handling policy
- Security-sensitive decisions
- Authentication and authorization changes
- Database schema and Alembic migrations
- Deployment and infrastructure
- Production import and Sheet import `--apply`
- Final decisions on legal or high-risk reporting policy
- Changes to CI permissions, secrets handling, and branch protection

## Maintainer and community review lead

**GitHub:** [@bgreg](https://github.com/bgreg)

**Responsibilities:**

- Contributor onboarding and issue triage
- Reviewing normal community pull requests within approved lanes
- Approving scoped test, documentation, bug-fix, validation, accessibility, and usability contributions
- Helping contributors keep changes within project scope
- Maintaining contribution quality
- Escalating security, privacy, data, deployment, and architecture changes to the project owner

Greg may approve and merge ordinary community contributions after required checks and code-owner review pass.

## Approval boundaries

The following require **explicit project-owner approval** before implementation:

- Authentication, authorization, and session handling
- Secrets, environment variables, and credential storage
- Database schema and Alembic migrations
- Production deployment, hosting, and infrastructure
- CI workflow permissions and security configuration
- Privacy policy and public report publication rules
- Production Sheet import, `--apply`, and any production data writes
- Changes that expose raw Form or Sheet submission data

Maintainers may close abusive, unsafe, duplicative, or unsupported submissions.

Maintainer status does not permit bypassing security, privacy, or review controls.

## Data boundaries

- Raw Google Form responses and Google Sheet moderation rows are **not** open-source project content.
- Private submission data must not be committed to the repository.
- Open-sourcing the code does not make private submission data public.

## Decision process

1. Contributors search existing issues and discuss scope before substantial work.
2. Draft pull requests are encouraged for uncertain or multi-file changes.
3. Required CI checks and CODEOWNERS review must pass before merge.
4. Sensitive paths listed in `.github/CODEOWNERS` require project-owner review.
5. Disputes on privacy, security, or reporting policy escalate to the project owner.

## Related documents

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [docs/reporting-and-moderation-policy.md](docs/reporting-and-moderation-policy.md)
- [docs/contributor-onboarding.md](docs/contributor-onboarding.md)
- [AGENTS.md](AGENTS.md)
