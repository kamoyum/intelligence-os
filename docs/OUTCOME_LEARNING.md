# Outcome Learning — v0.7.2-alpha

## Why this exists

Memory is not learning. Saving more conversations only increases available context. Outcome Learning closes the loop between what the human/AI system expected and what actually happened.

## Data model

- **Expectation**: prediction, expected result, confidence, horizon.
- **Decision**: what was chosen and why; may link to an expectation.
- **Outcome**: what happened, when, and a human-entered match score.
- **Lesson**: proposed interpretation/rule update plus outcome mismatch.

## Safety invariant

`Outcome → Lesson proposal` may be automated.

`Lesson proposal → reusable Memory` requires explicit human acceptance.

This prevents the system from silently turning a noisy single event into a permanent rule.

## Outcome mismatch and surprise

For the alpha implementation:

`outcome_mismatch = |prediction confidence - outcome match score|`

This is intentionally simple and transparent. It is a process metric, not a statistically validated forecast score.

## Future direction

- domain-aware outcome metrics;
- repeated-event aggregation before generalization;
- Brier/log scoring for probabilistic predictions where appropriate;
- explicit assumption tracking;
- causal caution: outcome association must not be mislabeled as causal learning;
- longitudinal calibration by skill/domain.


## Metric semantics
`outcome_mismatch = 1 - match_score` is a human-scored deviation from the expected result. `surprise_score = confidence × outcome_mismatch` weights that deviation by prior confidence. These are **not statistical calibration metrics** such as Brier score or log loss. Proper calibration requires repeated probabilistic forecasts with objectively scored outcomes.
