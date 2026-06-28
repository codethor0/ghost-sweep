# Scoring Algorithm

ghost-sweep uses transparent, testable risk signals rather than black-box accusations.

## Principles

- Every score includes raw inputs, weighted calculation, confidence, last updated timestamp, and user-facing explanation
- Language emphasizes risk signals, not legal findings
- Employer verification and disputes can reduce a score
- Reviewed evidence increases confidence

## Inputs

| Input | Description |
| ----- | ----------- |
| report_count | Total reports linked to the posting |
| reviewed_report_count | Reports with a reviewed timestamp |
| days_since_first_seen | Age of the posting record |
| days_since_last_repost | Days since the posting was last observed |
| duplicate_report_count | Number of duplicate category groups |
| verification_status | unverified, evidence_reviewed, disputed, verified_active |

## Weighted components

| Component | Weight |
| --------- | ------ |
| report_volume | 0.30 |
| reviewed_reports | 0.25 |
| repost_age | 0.20 |
| posting_staleness | 0.15 |
| duplicate_reports | 0.10 |

Each component is normalized to a 0..1 range before weighting.

## Verification adjustments

| Status | Adjustment |
| ------ | ---------- |
| unverified | 0.00 |
| evidence_reviewed | +0.15 |
| disputed | -0.20 |
| verified_active | -0.35 |

The final score is clamped to 0..1 after adjustment.

## Confidence calculation

Confidence starts at 0.35 and increases when:

- at least one report exists
- at least one reviewed report exists
- verification status is not unverified

## User-facing language

Use:

- Risk signal
- Reported by users
- Unverified
- Verified active
- Disputed
- Evidence reviewed

Avoid:

- Fraud
- Criminal
- Scam company
- Fake company

## Test coverage

Scoring tests live in `backend/tests/test_scoring.py` and must be updated whenever weights or adjustments change.
