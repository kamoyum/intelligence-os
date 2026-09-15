# Start here — Intelligence OS v0.7.2-alpha

## Fastest way to try it

### macOS
Double-click `START_MAC.command`.

### Windows
Double-click `START_WINDOWS.bat`.

### Linux
Run `./START_LINUX.sh`.

The launcher installs dependencies, runs a **preflight check**, and then opens the Desktop Core. Browser capture is optional.

## First useful experiment

1. Create one human Goal in the Console/API (for example, a research or project goal).
2. Capture a few relevant and irrelevant pages/notes.
3. Check **Attention**. Relevant information should rise because it matches your Goal, not just because it was recently saved.
4. Ask a stable question and a current-information question.
5. Check the Executive Plan: autonomy, evidence requirement, Query Safety, Skills, and Human role.
6. Verify a factual Claim and inspect Sources/Evidence/contradictions.
7. Record an Expectation with a due date; overdue outcomes should later surface in Brief.

## Privacy behavior to test

- Normal public query: external reasoning/research may run when configured.
- Sensitive query: external research/reasoning requires an explicit one-request permission.
- Secret/credential-like query: external transmission is blocked until the query is redacted/rephrased.
- Gmail/Drive/Calendar Memory remains hard-local in the current alpha.

## Mechanism checks

```bash
PYTHONPATH=backend pytest -q
PYTHONPATH=backend python scripts/simulate_cognitive_guardrails.py
PYTHONPATH=backend python scripts/benchmark_kernel.py
```

The Guardrail simulation checks that:
- a human Goal changes Attention ranking,
- credential-like text cannot be externally researched even with an explicit flag,
- common secret/PII patterns are redacted by the local helper,
- overdue Outcomes are surfaced.

The benchmark fixes representative Executive/Verification behavior so future changes cannot silently weaken the Kernel.

## Important interpretation

A web search is **evidence acquisition**, not proof. A `verified` Claim means the current evidence policy found sufficiently direct higher-authority support; it does not mean universally true.

Outcome Learning is **human-supervised reflective learning**. Accepted lessons become private Memory; proposed/rejected lessons do not silently become knowledge.


## Development rule
This build uses **Safety-Limited Velocity**: capability/authority does not expand merely because a feature works. See `docs/DEVELOPMENT_GOVERNANCE.md`.
