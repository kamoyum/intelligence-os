# Intelligence OS v0.7.2-alpha

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **Experimental Personal Cognitive Infrastructure** — local-first memory, context, verification, outcome learning, and bounded automation designed to augment human thinking without silently expanding authority.

**Status: Developer Alpha. Not production-ready.** Use synthetic or non-sensitive data only. Do not use identifiable patient data, workplace secrets, credentials, or other sensitive production data.

CI and CodeQL checks are configured for this repository. Contributions welcome.

## Looking for reviewers and contributors

Intelligence OS is a Developer Alpha.

We welcome:
- architecture review
- privacy and security review
- safety review
- eval design
- red-team cases
- failure cases
- documentation improvements
- macOS / Windows real-device validation
- Chrome / Edge Native Messaging testing
- accessibility and UX feedback

Criticism is welcome.
Finding a failure mode is a contribution.

Contributions must not weaken privacy boundaries, human authority, verification requirements, rollback capability, or safety-limited development governance.

## Why this project exists

Intelligence OS explores a local-first loop from perception and memory through context, attention, executive routing, skills, research, verification, human authority, bounded action, outcomes, learning, and system evals. The goal is not maximum autonomy. The goal is **trusted cognitive continuity**.

## Core principles

1. **Automate toil.** Repetitive, reversible, low-risk cognitive work should be cheap.
2. **Augment thinking.** High-value reasoning should improve human thinking, not replace it by default.
3. **Preserve human agency.** Consequential authority remains human-governed.
4. **Verify before trust.** Model confidence is not evidence.
5. **Memory is not truth.** Stored knowledge may become stale, contradicted, or superseded.
6. **Learn from outcomes.** Reusable lessons require real outcomes and explicit human acceptance.
7. **Capability ≠ authority.** More capability does not automatically grant more permission.
8. **Expand authority slowly.** Higher-risk, external, and irreversible behavior moves through explicit gates.

See [`INTELLIGENCE_OS.md`](INTELLIGENCE_OS.md) for the project constitution.

## What is implemented today

- Local Memory with SQLite / FTS retrieval
- Goal-aware Attention and Executive routing: `AUTO` / `AUGMENT` / `HUMAN CONTROL`
- Adaptive Evals and evidence-centered verification
- Query Safety: `safe` / `sensitive` / `secret`
- Human correction and supersession; accepted lessons only become reusable Memory
- Local reversible automation; external and consequential actions remain proposal-only
- Native Messaging allowlist and localhost boundaries
- Capability Gate: `HOLD` / `CONTAINED_ALPHA` / `ELIGIBLE_FOR_BOUNDED_EXPANSION`
- Safety-Limited Velocity development policy

## Architecture

```text
WORLD → PERCEPTION → MEMORY → CONTEXT → ATTENTION → EXECUTIVE → SKILLS
                                                       ↓
                         RESEARCH / REASONING → VERIFICATION → HUMAN AUTHORITY
                                                       ↓
                         BOUNDED ACTION → OUTCOME → LEARNING → SYSTEM EVALS
```

```text
Browser / Desktop / Mobile (planned)
                ↓
         Local Desktop Core
                ↓
 Cognitive Kernel + Knowledge + Bounded Tools
                ↓
 Privacy / Evals / Audit / Human Authority
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Validation

```bash
python scripts/public_repo_audit.py
python scripts/verify_version_sync.py
pytest
PYTHONPATH=backend python scripts/benchmark_kernel.py
PYTHONPATH=backend python scripts/benchmark_redteam.py
PYTHONPATH=backend python scripts/benchmark_development_governance.py
```

The repository also contains scenario simulations for kernel behavior, current research, outcome learning, cognitive guardrails, observability, and useful automation. Passing tests describe tested conditions only; they are not proof of safety or production readiness.

## Repository map

```text
backend/        FastAPI core + cognitive kernel
extension/      Chrome/Edge side-panel extension
native_host/    Native Messaging bridge
desktop/        local desktop runtime
benchmarks/     behavioral benchmark cases
scripts/        simulations, benchmarks, release checks
docs/           architecture, safety, research, learning, roadmap
.github/        CI, issue templates, PR template
```

## Contributing

Contributions are welcome at the **Developer Alpha** level, especially tests, evals, threat modeling, documentation, reproducibility, privacy boundaries, real-device validation, and failure cases. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Security reports

Do not post secrets, patient data, credentials, or exploit details in a public issue. See [`SECURITY.md`](SECURITY.md) for the disclosure process.

## License

Intelligence OS is licensed under the Apache License 2.0.

See [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

**Current stage:** `v0.7.2-alpha` · Developer Alpha · experimental · verification-centered · local-first · bounded automation · safety-governed
