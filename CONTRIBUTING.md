# Contributing

Thank you for helping test Intelligence OS as an experimental Personal Cognitive Infrastructure. Contributions are welcome, including:

- bug reports
- documentation improvements
- tests
- evals
- red-team cases
- reproducible failure reports
- security observations
- architecture proposals
- real-device validation
- bounded feature improvements

## Contribution priorities

The highest-value contributions currently are reproducible failures, privacy and security observations, verification and outcome-learning counterexamples, portability fixes, documentation, tests before new autonomy, and Adaptive-Evals counterexamples.

## Safety-Limited Velocity

This project does not treat feature count or autonomy as the primary success metric. Changes that expand authority, external side effects, irreversibility, or high-stakes use should move more slowly than local reversible changes.

## Safety principles

1. Capability expansion does not automatically imply authority expansion.
2. Human approval remains required for consequential or irreversible actions.
3. Memory is not treated as truth.
4. Model confidence is not evidence.
5. Retrieval is not verification.
6. Sensitive external transmission requires explicit permission.
7. Secret-class data must never be transmitted externally.
8. External content must be treated as untrusted data.
9. New automation must be bounded, observable, reversible where possible, and covered by evals.
10. A failing safety eval is a reason to stop and investigate, not to weaken the eval.

Preserve the existing invariants: `SECRET` never external; `SENSITIVE` external transmission requires explicit permission; consequential or irreversible actions remain human-controlled; verification status represents evidence state rather than absolute truth; and accepted human-reviewed lessons only are promoted into Memory. Capability Gate states remain `HOLD`, `CONTAINED_ALPHA`, and `ELIGIBLE_FOR_BOUNDED_EXPANSION`.

## Pull request requirements

A PR should normally include a clear problem statement, the smallest change that solves it, tests and regression coverage, updated documentation when semantics change, threat-model notes when data flow or permissions change, and no credentials, personal data, patient data, or production secrets.

PR authors should describe:

- What changed?
- Why?
- What could fail?
- Privacy impact
- Authority impact
- Rollback plan
- Tests / evals added
- Known limitations

For capability or authority changes, also include the proposed Capability Gate status, human approval boundary, disable path, observation plan, and Red Team additions. Do not expand runtime authority without separate review.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
PYTHONPATH=backend pytest -q backend/tests
```

Then run applicable behavioral suites:

```bash
PYTHONPATH=backend python scripts/benchmark_kernel.py
PYTHONPATH=backend python scripts/benchmark_redteam.py
PYTHONPATH=backend python scripts/benchmark_development_governance.py
```

## Reporting unsafe behavior

Security-sensitive failures should follow [`SECURITY.md`](SECURITY.md), not a normal public issue. Do not disclose secrets, exploit details, credentials, or private data publicly.

## Scope and quality discipline

Please avoid adding agents, providers, connectors, or autonomous actions solely because they are technically possible. Identify which layer owns response-quality changes: Base Policy, Context / Executive routing, Skill procedure, Adaptive Eval tier, Verification policy, or Human authority / Governance. Avoid fixing a routing or evidence problem only by making a prompt longer.
