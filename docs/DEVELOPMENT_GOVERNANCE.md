# Development Governance — Safety-Limited Velocity

## Position

Intelligence OS does **not** treat faster capability growth as a goal by itself.

The development rule is:

> **Advance only as fast as evidence, safeguards, rollback, and human governance can keep up.**

This is not a permanent halt doctrine. It is a bias toward slowing, containing, or holding a capability when safety evidence lags capability or authority.

## Why this is now explicit

Recent frontier-AI governance has increasingly used capability thresholds, safety cases, pre-deployment evaluations, incident reporting, and the option to delay/slow development when safeguards are not ready. The 2026 International AI Safety Report also highlights an evaluation gap and notes that development pace can pressure institutions to prioritise speed over risk management.

Relevant public references:
- International AI Safety Report 2026: https://internationalaisafetyreport.org/publication/international-ai-safety-report-2026
- OpenAI, "Pacing model development in an era of cyber-critical capabilities" (2026-08-18): https://openai.com/index/pacing-model-development-cyber-capabilities/
- OpenAI Preparedness Framework: https://openai.com/index/updating-our-preparedness-framework/
- Anthropic Responsible Scaling Policy (updated 2026): https://www.anthropic.com/responsible-scaling-policy

There is a real counterargument: excessive slowing can reduce useful innovation and may create competitive/geopolitical disadvantages. Intelligence OS therefore uses **risk-proportional pacing**, not blanket stagnation.

## Governance invariants

1. **Safety regression freezes expansion.**
   - privacy regression => HOLD
   - safety benchmark regression => HOLD
   - open critical incident => HOLD

2. **Authority expands more slowly than capability.**
   A model may become better at proposing an action without automatically gaining permission to execute it.

3. **One new authority boundary at a time.**
   Default release budget: at most one new authority boundary per release.

4. **External writes need observation evidence.**
   External-write capability stays contained until it has a sufficient observation window and real-world evidence.

5. **Irreversible autonomy is blocked.**
   If an operation cannot be rolled back, it is not eligible for autonomous execution under the current policy.

6. **Missing evidence is not permission.**
   Uncertainty moves a capability toward CONTAINED_ALPHA or HOLD, not toward expansion.

## Capability gate states

### HOLD
Do not expand capability or authority. Fix the blocker first.

Typical triggers:
- critical incident
- privacy regression
- safety benchmark regression
- permission expansion without separate governance
- irreversible autonomous action
- too many authority boundaries introduced at once

### CONTAINED_ALPHA
The capability may be tested in a bounded environment but does not gain broader authority.

Typical triggers:
- incomplete Evals/Red Team coverage
- insufficient live observation
- no real-world evidence yet
- high-risk capability with no production safety case

### ELIGIBLE_FOR_BOUNDED_EXPANSION
Evidence is sufficient to widen a bounded test. This is **not** blanket production approval.

## Development pace is itself evaluated

A release is considered better only if it improves at least one of:
- safety evidence
- usefulness
- cognitive-agency preservation
- reversibility
- observability
- verification quality

Feature count and release frequency are not success metrics.
