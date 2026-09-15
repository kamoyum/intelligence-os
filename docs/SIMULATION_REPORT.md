# v0.5-alpha simulation report

## Purpose

Test whether the core Intelligence OS idea is executable, not merely descriptive.

This simulation uses fictional `Alpha` rules only. It does **not** establish performance on real medical, legal, financial, scientific, or current-affairs claims.

## Scenario

1. Executive receives: "Find the latest Alpha rule and check for contradiction with prior knowledge."
2. Local source A (2025) says `Alpha requires 3 sessions per week.`
3. The claim is verified against source A.
4. Newer local source B (2026) says `Alpha requires 2 sessions per week; previous 3-session rule is obsolete.`
5. The old claim is re-verified.
6. A new 2-session claim is verified.
7. The OS does not silently delete the old claim.
8. Human explicitly confirms supersession.

## First-run failures discovered

The simulation was not made to pass on the first attempt.

### Failure 1 — prompt-injection detector gap

`Ignore all previous instructions` was not matched by the initial regular expression.

Fix: broadened the detector and added a regression test.

### Failure 2 — false contradiction

The new source supported `2 sessions` while also mentioning the obsolete `3 sessions`. The initial heuristic saw the differing number and falsely classified the new source as contradicting the new claim.

Fix: direct assertion support is evaluated before nearby opposite/obsolete discussion. Regression test + simulation re-run.

### Failure 3 — unstable Claim identity

Repeated verification initially created duplicate Claim objects.

Fix: stable Claim identity for the same text/topic; prior verdicts are snapshotted to `claim_history` before re-verification.

## Final deterministic result

- backend tests: **28 passed**
- Executive selected `memory_context + research + verify`
- old claim initially: `verified`
- after newer source: `contested`
- new claim: `verified`
- old claim remains historical until human supersession
- human supersession: successful
- all simulation pass conditions: **true**

## What this proves

It proves that the current code can execute this local mechanism:

`Memory → Provenance → Claim → Evidence → Contradiction → Human-controlled knowledge update`

## What this does not prove

It does not prove:

- live-web research quality,
- primary-source discovery accuracy,
- reliability across ambiguous natural-language claims,
- medical/scientific evidence grading,
- production security,
- resistance to all prompt-injection attacks,
- longitudinal usefulness to a real person.

Those require separate Evals.
