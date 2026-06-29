# Scoring Algorithm

ghost-sweep publishes transparent scores on a 0 to 100 scale. Scores are risk signals and integrity signals, not legal findings.

## Job Ghost Risk Score

Range: 0 to 100. Higher values indicate stronger ghost-job risk signals.

## Inactive scoring inputs (current implementation)

The scoring engine in `backend/app/services/scoring.py` supports all documented components. The scoring pipeline (`scoring_pipeline.py`) passes fixed defaults for inputs that do not yet have live data sources. These components appear in breakdowns but contribute zero or default points until a future batch wires real inputs.

| Input field | Score component | Pipeline default | Effect today |
| ----------- | --------------- | ---------------- | ------------ |
| `language_risk_signal` | language_risk_signals (max 10) | `0.0` | **Inactive — contributes 0 points** |
| `recruiter_follow_through_rate` | recruiter_follow_through (max 10) | `0.0` | **Inactive — contributes 0 points** |
| `correction_count` | correction_history (max 5) | `0` | **Inactive — contributes 0 points** |
| `average_days_to_fill` | average_time_to_fill (max 10) | `None` | **Deferred — uses 5-point default when null** |

Future batches may add language analysis, recruiter follow-through metrics, correction tracking, and fill-time ingestion. Until then, documented weights apply only when non-default inputs are supplied (for example in unit tests).

### Components

| Component | Max points | Input signal |
| --------- | ---------- | ------------ |
| posting_age | 25 | Days since posting detected, capped at 180 days |
| repost_history | 20 | Repost count, capped at 8 reposts |
| company_history | 15 | Inverse of company integrity score |
| verified_report_evidence | 15 | Count of verified reports, capped at 5 |
| language_risk_signals | 10 | Normalized 0..1 language analysis signal |
| no_response_reports | 10 | Count of no-response reports, capped at 4 |
| interview_without_offer_pattern | 5 | Count of fake-interview reports, capped at 3 |

### Adjustments

- `filled` postings reduce posting age and repost contributions to 25 percent of normal
- `disputed` postings reduce verified report evidence to 50 percent of normal

### Formula

Each component is scaled to its max points, summed, then clamped:

```text
total = clamp(sum(breakdown.values()), 0, 100)
```

### Example

Inputs:

- posting age: 200 days
- repost count: 6
- company integrity score: 25
- verified reports: 4
- language risk signal: 0.8
- no-response reports: 3
- fake-interview reports: 2
- status: active

Expected result: score at or above 70 with non-zero values in posting age, repost history, and verified report evidence.

## Company Integrity Score

Range: 0 to 100. Higher values indicate stronger integrity signals.

### Components

| Component | Max points | Input signal |
| --------- | ---------- | ------------ |
| post_to_hire_ratio | 25 | hires / postings, capped at 1.0 |
| report_ratio | 20 | inverse of verified reports / postings |
| response_rate | 15 | employer responses / total reports |
| verification_status | 15 | verified=15, unverified=7.5, disputed=3 |
| average_time_to_fill | 10 | faster fill earns more points |
| recruiter_follow_through | 10 | normalized follow-through rate |
| correction_history | 5 | correction count capped at 5 |

### Zero-division safety

- post-to-hire ratio uses 0 when postings = 0
- report ratio uses 0 when postings = 0
- response rate uses denominator max(reports, 1)
- missing average time to fill defaults to 5 points

### Example

Inputs:

- postings: 20
- hires: 15
- verified reports: 0
- total reports: 1
- employer responses: 1
- verified status: verified
- average days to fill: 30
- follow-through rate: 0.9
- corrections: 2

Expected result: score at or above 80.

## Confidence model

Scoring formulas are implemented in `backend/app/services/scoring.py`.

Batch 5 wires scoring recalculation to report and vote writes and persists score snapshots. Score read endpoints return current score breakdowns without persisting on read.

Future work may expand confidence modeling, moderation integration, and evidence weighting. Potential inputs include:

- count of verified reports
- presence of employer responses
- evidence file count and hash verification
- moderation outcome history

## Edge cases

| Case | Expected behavior |
| ---- | ----------------- |
| Zero postings for company | post-to-hire and report ratio components use safe defaults |
| Zero reports | response rate uses denominator 1 |
| Missing fill-time data | average time to fill defaults to 5 points |
| Extreme input values | all totals clamp to 0..100 |
| Filled posting | age and repost risk reduced |

## Test coverage

Scoring tests live in `backend/tests/test_scoring.py` and must be updated whenever weights or caps change.

Current batch includes 12 test cases covering clamping, zero-division safety, status adjustments, and verified report counting.

## Language standards

Use:

- risk signal
- reported by users
- unverified
- verified
- disputed
- evidence reviewed

Avoid:

- fraud
- criminal
- scam company
- fake company
