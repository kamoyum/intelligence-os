# Development Governance

## Safety-Limited Velocity

Intelligence OS intentionally develops at the speed its **safety evidence, evaluation, rollback, and human governance** can support — not simply at the maximum speed models or tools make possible.

This is not a blanket freeze on development.

### Move faster when

- the change is local
- low-risk
- reversible
- easy to test
- does not expand authority
- failure is observable and recoverable

### Move slower when

- the change affects third parties
- it writes to external systems
- it is difficult to undo
- it changes privacy boundaries
- it increases autonomous authority
- it affects high-stakes domains
- the evidence base is weak

## Capability is not authority

A model can become more capable without receiving more permission.

```text
Capability increase
      ≠
Authority increase
```

External authority should be governed independently.

## Capability Gate

### HOLD

Use when any of the following are true:

- privacy regression
- safety benchmark regression
- uncontrolled authority expansion
- irreversible automation without recovery
- unresolved high-severity incident
- missing tests for a new high-risk path

### CONTAINED_ALPHA

Appropriate when:

- behavior is bounded
- test coverage exists
- human authority is preserved
- failure is recoverable
- real-world evidence is still limited

### ELIGIBLE_FOR_BOUNDED_EXPANSION

Requires stronger evidence, including:

- stable benchmarks
- Red Team coverage
- rollback path
- observation period
- real-device / live-provider evidence where relevant
- explicit review of authority boundaries

Eligibility does **not** automatically authorize deployment.

## Default authority budget

The project defaults to **at most one new authority boundary per release**. Capability-only releases are preferred when safety evidence is still catching up.

## Human cognitive agency

Automation should not be evaluated only by speed or task completion. The system also tracks whether it:

- helped the user think
- saved repetitive work
- caught an error
- made the user think less
- felt unsafe

A faster system that persistently reduces healthy human reasoning can fail the project's North Star even when its task metrics improve.

## Release rule

A release can be delayed or blocked by safety/evaluation failures even if the feature itself works technically.


## Adaptive evaluation governance

The project does not spend identical evaluation effort on every task. Eval intensity scales with consequence and uncertainty, but the Base Policy never turns off.

A feature may not lower a High-Stakes task to a lighter profile merely to reduce latency or cost. Changes to tiering rules require regression cases that demonstrate both over-escalation and under-escalation behavior.
