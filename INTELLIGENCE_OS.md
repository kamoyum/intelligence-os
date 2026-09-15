# Intelligence OS Manifest

## Purpose

Intelligence OS exists to **reallocate human cognitive resources toward higher-value thinking** while safely automating repetitive, low-value cognitive work.

It is not a system for making humans think less. It is a personal cognitive infrastructure that helps people remember context, investigate efficiently, verify claims, retain agency, and learn from outcomes.

## North Star

> Automate what does not deserve human attention. Augment what benefits from human thinking. Preserve human authority where values, uncertainty, consequences, or meaning matter.

## Kernel

1. **Memory** — What has been observed, decided, and learned?
2. **Context** — What should be remembered now?
3. **Executive** — What kind of cognitive work is this, and what deserves human attention?
4. **Skills** — Which reusable procedure should be applied?
5. **Adaptive Eval Policy** — How much checking does this task deserve, without weakening the Base Policy?
6. **Research / Reasoning** — What can be inferred, and what must be investigated?
7. **Verification** — What is actually supported, current, and non-contradictory?
8. **Governance** — What may the system see, share, or do?
9. **Outcome** — What happened in reality?
10. **Learning** — What should change next time?

## Automation doctrine

### AUTO
Use for low-risk, reversible, low-value cognitive work:
- extraction
- formatting
- deduplication
- routine retrieval
- summarization that preserves meaning
- local organization

### AUGMENT
Use where human cognition is valuable:
- hypothesis formation
- research interpretation
- strategy
- clinical reasoning
- comparison and trade-offs
- creative work
- consequential planning

AI supplies context, evidence, alternatives and critique. The human retains interpretation and judgment.

### HUMAN CONTROL
Use where consequence, irreversibility, values, permissions or high-stakes decisions dominate:
- external sending/publishing
- irreversible deletion
- permission escalation
- purchases/contracts
- high-stakes medical/legal/financial decisions

AI may advise. It does not silently take authority.

## Core principles

- **Human cognitive agency > maximum automation**
- **Relevant Context > Maximum Context**
- **Evidence > Model confidence**
- **Base Policy is always-on; Eval intensity is adaptive**
- **Evaluation != Verification**
- **Memory is not truth**
- **Memory != External LLM Context**
- **Outcome > Output**
- **Skills > one-off prompts**
- **Reversible automation > irreversible automation**
- **Simple experience > exposed system complexity**
- **Measured usefulness > feature count**

## Never

- silently expand permissions
- treat retrieved memory as verified truth
- hide whether an eval is heuristic or evidence-based
- automate a high-value judgment merely because a model can produce an answer
- add complexity without a measurable benefit
- make critical external actions without explicit human authority

## Long horizon

The long-term direction is not an artificial human brain or a company of permanent AI employees.

It is an adaptive **Human + Machine cognitive system** in which:
- machines absorb repetitive cognitive overhead,
- humans retain agency, judgment, meaning and creativity,
- shared work produces explicit outcomes,
- the system learns from errors without silently rewriting human values.


## Development pace doctrine — Safety-Limited Velocity

Intelligence OS does not optimize for maximum development speed. It advances only as fast as **evidence, safeguards, rollback, observability, and human governance can keep up**.

- capability growth does not imply authority growth
- safety/privacy regressions freeze expansion
- missing evidence moves a feature toward containment, not permission
- irreversible autonomy is not eligible for expansion
- default authority budget is one new authority boundary per release
- feature count and release frequency are not success metrics

This is a **risk-proportional slowing principle**, not a blanket ban on innovation. Low-risk reversible improvements may move quickly; capabilities that alter permissions, external systems, or high-stakes decisions move deliberately.

## Research doctrine added in v0.5-beta

- Search is a discovery mechanism, not a truth oracle.
- Current information should be fetched into Provenance before it influences verified Knowledge.
- Primary/official-looking sources are preferred, but authority metadata never replaces evidence assessment.
- Research may be automated when low-risk and bounded; sensitive/high-risk query disclosure returns to human control.
- Provider/network failure must reduce capability explicitly, never trigger fabricated freshness.


## Outcome Learning doctrine added in v0.6-alpha

- Memory is not learning. Learning requires an expectation and a real outcome.
- A mismatch should trigger reflection, not automatic self-modification.
- One result does not prove causality or a universal rule.
- The OS may propose a lesson; the human decides whether it becomes reusable personal Knowledge.
- Accepted learning should remain traceable to the expectation, decision and outcome that produced it.

## Quality architecture inherited from custom-instruction work

Earlier custom-instruction experiments established durable policies: do not fabricate, prefer primary evidence when freshness matters, distinguish verified/inferred/unverified states, check counterevidence for important decisions, calibrate conclusion strength to evidence, and correct errors explicitly.

Intelligence OS no longer relies on those ideas as a long prompt alone. They are separated into:

1. **Base Policy** — always-on quality floor.
2. **Context / Executive / Skills** — orchestration of the cognitive workflow.
3. **Adaptive Eval Policy** — Light / Standard / Deep / High-Stakes evaluation intensity selected before/around execution.
4. **Post-execution Evaluation** — Quality checks applied to outputs; this remains distinct from evidence-based Verification.
5. **Verification** — evidence-based claim assessment independent of model confidence.
6. **Correction / Learning** — failures become explicit updates or regression cases.

See [`BASE_POLICY.md`](BASE_POLICY.md) and [`QUALITY_HARNESS.md`](QUALITY_HARNESS.md).
