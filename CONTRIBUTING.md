# Contributing

Thank you for helping test Intelligence OS as an experimental Personal Cognitive Infrastructure.

## Contribution priorities

The highest-value contributions currently are:

1. reproducible bug reports
2. privacy / security failures
3. Red Team cases
4. verification failure cases
5. Executive-routing counterexamples
6. outcome-learning failure cases
7. setup / portability fixes
8. documentation that reduces ambiguity
9. tests before new autonomy
10. Adaptive-Evals counterexamples (tasks routed too lightly or too heavily)

## Safety-Limited Velocity

This project does not treat feature count or autonomy as the primary success metric.

Before proposing a change, ask:

- Does this increase **capability** only, or also **authority**?
- Is the action local or external?
- Is it reversible?
- Could it leak sensitive information?
- Could failure harm a person or third party?
- What test or observation would falsify our belief that it is safe/useful?
- What is the rollback path?

Changes that expand authority, external side effects, irreversibility, or high-stakes use should move more slowly than local reversible changes.

## Pull request requirements

A PR should normally include:

- a clear problem statement
- the smallest change that solves it
- tests for the new behavior
- regression coverage for the failure being fixed
- updated documentation if semantics changed
- threat-model notes if data flow, permissions, or tools changed
- no credentials, personal data, patient data, or production secrets

For a capability/authority expansion, also include:

- proposed Capability Gate status
- human approval boundary
- rollback / disable path
- observation plan
- Red Team additions

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
PYTHONPATH=backend pytest -q backend/tests
```

Then run the behavioral suites:

```bash
PYTHONPATH=backend python scripts/benchmark_kernel.py
PYTHONPATH=backend python scripts/benchmark_redteam.py
PYTHONPATH=backend python scripts/benchmark_development_governance.py
```

## Reporting unsafe behavior

Security-sensitive failures should follow [`SECURITY.md`](SECURITY.md), not a normal public issue.

## Scope discipline

Please avoid adding agents, providers, connectors, or autonomous actions solely because they are technically possible. New complexity should demonstrate measurable value against the project's North Star: **reallocate human cognitive resources toward higher-value thinking while preserving human agency.**


## Quality-layer discipline

When changing response quality behavior, identify which layer owns the change:

- Base Policy
- Context / Executive routing
- Skill procedure
- Adaptive Eval tier
- Verification policy
- Human authority / Governance

Avoid fixing a routing or evidence problem only by making a prompt longer.
