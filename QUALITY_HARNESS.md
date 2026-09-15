# Quality Harness

Intelligence OS uses a layered quality architecture:

```text
Context
  ↓
Reasoning
  ↓
Execution
  ↓
Evaluation
  ↓
Correction
  ↺
```

The project deliberately separates **Base Policy**, **Orchestration**, and **Evals Harness**.

## 1. Base Policy — always on

See [`BASE_POLICY.md`](BASE_POLICY.md).

This is the minimum quality floor: anti-fabrication, epistemic-state separation, evidence/conclusion calibration, uncertainty, correction, and human authority.

## 2. Orchestration — choose the right cognitive workflow

The Executive and Skills layers decide:

- what the user is actually trying to achieve
- whether current information is needed
- whether Research / Verification is required
- whether work should be `AUTO`, `AUGMENT`, or `HUMAN CONTROL`
- what must remain human judgment
- when to stop

This is Context Engineering / Harness Engineering rather than one-shot prompt engineering.

## 3. Adaptive Evals — scale checking effort

Not every question should pay the same evaluation cost.

### Level 1 — Light

Use for low-risk, stable, mostly mechanical work.

Examples:
- formatting
- extraction
- faithful summarization
- low-risk organization

Checks:
- faithfulness
- completeness
- meaning preservation

External judge: normally skipped.

### Level 2 — Standard

Use for ordinary comparisons, explanations, and moderate-value decisions.

Checks:
- assumptions
- relevance
- trade-offs
- obvious factual inconsistencies

External judge: optional.

### Level 3 — Deep

Use when the answer depends on current rules, evidence, research, or consequential comparison.

Examples:
- current technical research
- tax / pension / investment-rule comparisons
- evidence-heavy design choices

Checks:
- primary-source preference
- current-source verification when needed
- counterevidence
- applicability / scope
- explicit uncertainty

External judge: preferred when privacy policy permits, but Verification remains independent.

### Level 4 — High-Stakes

Use for health, legal, critical safety, credential/privacy boundaries, or other high-consequence decisions.

Checks:
- stronger evidence requirements
- counterevidence / alternative explanations
- current primary sources when applicable
- explicit human decision point
- no silent authority expansion

External judge: may assist, but cannot replace Verification or human authority.

## Important separation

**Evaluation is not Verification.**

An LLM judge can rate clarity or groundedness, but it cannot transform unsupported external claims into verified facts.

**Custom instructions are not the Evals Harness.**

Custom instructions set defaults. The Harness applies reproducible task-specific evaluation logic.

**Prompt Engineering is inside Context Engineering.**

The prompt matters, but so do retrieved context, tool choice, source boundaries, Skill selection, risk policy, stop conditions, and evaluation.

## Current implementation

`backend/intelligence_os/quality_harness.py` assigns an Eval Profile from Executive signals.

The profile is attached to the Executive Plan and surfaced in `/api/plan` and `/api/ask`.

The Base Policy is also injected into the reasoning core through `backend/intelligence_os/base_policy.py`.
