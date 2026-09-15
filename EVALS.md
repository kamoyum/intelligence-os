# Evals and Evidence

Intelligence OS treats evaluation as part of the product, not as a release afterthought.

## Layers of evaluation

## Adaptive Evals

Evaluation intensity is selected by the Quality Harness rather than by a fixed “always maximum” policy.

- **Level 1 — Light:** low-risk stable transformations; local heuristic checks are normally sufficient.
- **Level 2 — Standard:** ordinary comparison / explanation / moderate-value judgment.
- **Level 3 — Deep:** current, research-heavy, financial-rule, or evidence-sensitive tasks; counterevidence and primary-source preference are expected.
- **Level 4 — High-Stakes:** health, legal, critical safety, secrets/privacy, or other high-consequence work; stronger evidence and explicit human judgment are required.

The always-on [`BASE_POLICY.md`](BASE_POLICY.md) applies at every level. A Light Eval does **not** permit fabrication or unsafe external action.

Adaptive Evals do not replace Verification. LLM/heuristic evaluation scores answer quality; Verification evaluates whether material claims are actually supported by evidence.


### 1. Unit / regression tests

Checks deterministic implementation behavior.

### 2. Cognitive-kernel benchmark

Representative cases for Executive routing and Verification status.

Current release-point benchmark:

- Executive / Adaptive Evals: 11 / 11
- Verification: 6 / 6

### 3. Red Team benchmark

Covers adversarial and boundary cases such as:

- secret / PII leakage
- unsafe authority expansion
- prompt injection
- SSRF-style fetch targets
- low-quality evidence promoted too strongly
- browser/native bridge overreach

Current release-point benchmark: 16 / 16.

### 4. Development-governance benchmark

Tests the Capability Gate and release-slowing policies.

Current release-point benchmark: 6 / 6.

### 5. Scenario simulations

Synthetic end-to-end scenarios cover:

- Knowledge Lifecycle
- Current-source Research
- HTTP Research routing
- Outcome Learning
- HTTP Outcome Learning
- Cognitive Guardrails
- Observability
- Useful Automation

### 6. Real-world alpha metrics

The next major evidence layer is longitudinal use, not additional synthetic architecture.

Planned metrics include:

- Memory reuse rate
- duplicate research avoided
- research success rate
- unresolved contradictions
- time-to-trusted-action
- overdue outcome follow-up
- lesson acceptance / later usefulness
- approval interventions
- `helped_me_think`
- `saved_repetitive_work`
- `made_me_think_less`
- `felt_unsafe`

## Important interpretation rule

**Passing Evals does not prove safety or truth.**

Tests only show that the system behaved as expected under the cases encoded so far. New failures should become new regression or Red Team cases whenever possible.

## `verified` semantics

`verified` means the current evidence policy found sufficiently direct support from sufficiently authoritative stored evidence. It does not mean globally true, independently replicated, or permanently correct.
