# Intelligence OS — Product Specification v0.7.2-alpha

## Product thesis

Intelligence OS is not designed to make humans stop thinking. It automates low-value cognitive overhead and preserves human attention for hypotheses, interpretation, creativity, values, and consequential judgment.

## North Star

> Reallocate human cognitive resources toward higher-value thinking while safely automating repetitive, low-value cognitive work.

## Kernel capabilities

1. Memory
2. Context
3. Executive
4. Skills
5. Adaptive Evals
6. Research / Reasoning
7. Verification
8. Governance
9. Outcome
10. Learning

## v0.5-alpha implemented path

```text
Capture
→ Provenance
→ Memory
→ Context retrieval
→ Executive plan
→ Skills
→ Reasoning
→ Claim extraction when Verify is selected
→ Local Evidence matching
→ Verification / Contradiction
→ Human correction / supersession
→ Audit
```

## Truth boundary

In v0.6-alpha, `verified` is reserved for sufficiently direct support from higher-authority stored evidence. Lower-authority support is labeled `supported`. `verified` still does not mean globally or independently proven true.

The UI/API therefore exposes `verification_scope=local_memory` and a limitations string.

## Human cognitive agency

- low-risk mechanical work may run automatically,
- high-value cognition is augmented rather than silently replaced,
- consequential external actions remain under human authority,
- knowledge history is corrected or superseded explicitly rather than silently rewritten.

## Success metrics

- repeated-context minutes saved
- duplicate investigations avoided
- useful-memory retrieval precision
- unsupported-claim rate
- contradiction detection rate
- correction/supersession accuracy
- time to trusted next action
- human override rate
- high-value thinking preserved or increased


## Quality architecture

The system separates an always-on Base Policy from task-specific Adaptive Evals. The Base Policy prevents fabrication, requires epistemic-state separation and preserves human authority. Adaptive Evals scale extra checking effort from Light to High-Stakes. Evaluation never substitutes for evidence-based Verification.
