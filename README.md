# Intelligence OS v0.7.2-alpha

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

> **Experimental Personal Cognitive Infrastructure** — local-first memory, context, verification, outcome learning, and bounded automation designed to augment human thinking without silently expanding AI authority.

**Status: Developer Alpha. Not production-ready.** Use synthetic or non-sensitive data only. Do **not** use identifiable patient data, workplace secrets, credentials, or other sensitive production information.


## In 30 seconds

**AI should remember context, verify claims, learn from outcomes, and still leave consequential authority with the person using it.**

Intelligence OS is an experimental, local-first cognitive layer for:

- **Memory** — preserve useful context across work instead of starting from zero
- **Verification** — track claims, evidence, contradictions, provenance, and uncertainty
- **Outcome learning** — connect expectations and decisions to what actually happened, then promote only human-accepted lessons
- **Bounded automation** — automate low-risk, reversible work while keeping consequential or irreversible actions human-controlled
- **Privacy boundaries** — classify queries as `safe`, `sensitive`, or `secret` before optional external reasoning or search
- **Adaptive evaluation** — scale checking effort with consequence without removing the always-on safety and anti-fabrication floor

### The design stance

| Tension | Intelligence OS stance |
| --- | --- |
| Memory vs. truth | **Memory is not truth.** Stored knowledge can become stale, contradicted, or superseded. |
| Capability vs. permission | **Capability ≠ authority.** Better models do not automatically get more permission. |
| Retrieval vs. evidence | **Retrieval is not verification.** Sources are evidence to assess, not instructions to obey. |
| Learning vs. silent self-modification | Reusable lessons require outcomes and explicit human acceptance. |
| Automation vs. control | Prefer bounded, observable, reversible actions; keep consequential authority with the human. |

### Try it

Start with [`START_HERE.md`](START_HERE.md). The current alpha supports local startup paths for macOS, Linux, and Windows, plus Chrome/Edge-side components. Use only synthetic or non-sensitive data during alpha testing.

If you review systems, privacy, security, evals, HCI, local AI, or agent governance, see [`CALL_FOR_REVIEW.md`](CALL_FOR_REVIEW.md). **Finding a failure mode is a contribution.**

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

Criticism is welcome. Finding a failure mode is a contribution.

Contributions must not weaken privacy boundaries, human authority, verification requirements, rollback capability, or safety-limited development governance.

## 日本語サマリー

Intelligence OS は、AIに「何でも考えさせる」ためのOSではありません。

目的は、**人間の認知資源を、より価値の高い思考へ再配分すること**です。

- 反復的・低価値・低リスクな作業はAIへオフロード
- 仮説、比較、研究、振り返りは Human + AI で協働
- 高リスク、不可逆、価値判断、権限変更は Human Lead
- 「記憶している」ことと「真実である」ことを分離
- 能力が増えても、権限は自動的に増やさない
- 開発速度は **Safety-Limited Velocity** — 安全性・検証・Rollback・人間の統治が追いつく範囲で進める

## Why this project exists

Most AI interactions still reset too easily: users repeatedly explain context, re-run searches, reconstruct decisions, and lose the relationship between a prediction and what actually happened later.

Intelligence OS explores a different loop:

```text
WORLD
  ↓
PERCEPTION
  ↓
MEMORY
  ↓
CONTEXT
  ↓
ATTENTION
  ↓
EXECUTIVE
  ↓
SKILLS
  ↓
RESEARCH / REASONING
  ↓
VERIFICATION
  ↓
HUMAN AUTHORITY
  ↓
BOUNDED ACTION
  ↓
OUTCOME
  ↓
LEARNING
  ↓
SYSTEM EVALS
  ↺
```

The goal is not maximum autonomy. The goal is **trusted cognitive continuity**.

## Core principles

1. **Automate toil.** Repetitive, reversible, low-risk cognitive work should be cheap.
2. **Augment thinking.** High-value reasoning should improve human thinking, not replace it by default.
3. **Preserve human agency.** Consequential authority remains human-governed.
4. **Verify before trust.** Model confidence is not evidence.
5. **Memory is not truth.** Stored knowledge may become stale, contradicted, or superseded.
6. **Learn from outcomes.** Reusable lessons require real outcomes and explicit human acceptance.
7. **Capability ≠ authority.** A system becoming more capable does not automatically grant it more permission.
8. **Expand authority slowly.** Higher-risk, external, and irreversible behavior moves through explicit gates.
9. **Scale evaluation to consequence.** The Base Policy is always on; Adaptive Evals increase checking effort for deeper or higher-stakes tasks.

See [`INTELLIGENCE_OS.md`](INTELLIGENCE_OS.md) for the project constitution.


## Quality architecture

Earlier custom-instruction work evolved into a layered quality system:

```text
Custom Instructions / Preferences
              ↓
       Always-on Base Policy
              ↓
 Context / Executive / Skills
              ↓
 Adaptive Evals (Light → High-Stakes)
              ↓
 Verification / Correction
```

- [`BASE_POLICY.md`](BASE_POLICY.md) defines the non-negotiable quality floor.
- [`QUALITY_HARNESS.md`](QUALITY_HARNESS.md) defines Adaptive Evals and the separation between evaluation and verification.
- [`docs/CUSTOM_INSTRUCTIONS_LINEAGE.md`](docs/CUSTOM_INSTRUCTIONS_LINEAGE.md) documents how the project evolved from prompt/custom-instruction work into Context and Harness Engineering.

The key rule is: **lighter Evals may reduce cost, never the safety or anti-fabrication floor.**

## What is implemented today

### Cognitive kernel

- Local Memory + SQLite / FTS retrieval
- Goal-aware Attention
- Executive routing: `AUTO` / `AUGMENT` / `HUMAN CONTROL`
- Adaptive Eval Profiles: `Light` / `Standard` / `Deep` / `High-Stakes`
- Always-on Base Policy independent of eval intensity
- Query Safety: `safe` / `sensitive` / `secret`
- Skills registry with maturity levels
- Human cognitive-agency feedback
- Unified Attention Queue

### Research and verification

- Optional current-source Web Research path
- Provenance, Claims, Evidence, Contradictions
- `supports` / `contradicts` / `unclear` evidence classification
- Human correction and supersession
- Source authority and publication-date handling
- Prompt-injection risk flags
- `verified` as an **evidence-policy status**, never as absolute truth

### Outcome learning

- Expectation → Decision → Outcome
- Outcome mismatch / surprise tracking
- Reflection lesson proposals
- Human accept/reject before a lesson becomes reusable Memory
- Overdue Outcome surfacing

### Bounded automation

- Low-risk local private-note creation
- Undo for local note actions
- External/consequential actions remain proposal-only
- Approval and action-run logs

### Safety / governance

- Local-first runtime
- Bearer-token protected localhost API
- Trusted Host / narrow CORS boundary
- Native Messaging allowlist
- Query-level privacy gate before external reasoning/search/evals/embeddings
- Red Team benchmark
- Capability Gate: `HOLD` / `CONTAINED_ALPHA` / `ELIGIBLE_FOR_BOUNDED_EXPANSION`
- Safety-Limited Velocity development policy

## What is **not** claimed

This repository does **not** claim:

- that `verified` means globally true
- that all external sources are trustworthy
- that prompt injection is solved
- that the system is safe for clinical production
- that the system is an autonomous medical/legal/financial decision maker
- that external side effects are production-hardened
- that passing tests proves real-world safety
- that Intelligence OS is a finished consumer product

## Quick start

### Requirements

- Python 3.11 or 3.12 recommended
- Chrome or Edge for the browser extension
- Optional: OpenAI API key for remote model / Web Research experiments
- Optional: Google OAuth credentials for connector experiments

### Start locally

macOS:

```bash
./START_MAC.command
```

Linux:

```bash
./START_LINUX.sh
```

Windows:

```bat
START_WINDOWS.bat
```

For source-level setup, see [`START_HERE.md`](START_HERE.md).

## Run the full evaluation suite

```bash
cd backend
PYTHONPATH=. pytest -q
cd ..

PYTHONPATH=backend python scripts/benchmark_kernel.py
PYTHONPATH=backend python scripts/benchmark_redteam.py
PYTHONPATH=backend python scripts/benchmark_development_governance.py
PYTHONPATH=backend python scripts/simulate_kernel.py
PYTHONPATH=backend python scripts/simulate_current_research.py
PYTHONPATH=backend python scripts/simulate_outcome_learning.py
PYTHONPATH=backend python scripts/simulate_cognitive_guardrails.py
PYTHONPATH=backend python scripts/simulate_observability.py
PYTHONPATH=backend python scripts/simulate_useful_automation.py
```

The release builder runs compile checks, tests, simulations, benchmarks, version synchronization, and archive hygiene checks before generating a distributable ZIP:

```bash
python scripts/build_release.py
```

## Current validated status

At the v0.7.2-alpha release point used to prepare this public repository:

- Unit / regression tests: **80 / 80 PASS**
- Executive / Adaptive-Evals benchmark: **11 / 11 PASS**
- Verification benchmark: **6 / 6 PASS**
- Red Team benchmark: **16 / 16 PASS**
- Development-governance benchmark: **6 / 6 PASS**
- Knowledge / Research / Outcome / Observability / Useful-Automation simulations: PASS

These results describe the **tested conditions only**. They are not a proof of safety, correctness, or fitness for production use.

## Architecture

```text
Browser / Desktop / Mobile (planned)
                ↓
         Local Desktop Core
                ↓
 ┌──────────────────────────────┐
 │ Cognitive Kernel             │
 │ Attention / Executive /      │
 │ Skills / Reasoning / Verify  │
 └──────────────────────────────┘
                ↓
 ┌──────────────────────────────┐
 │ Knowledge                    │
 │ Memory / Source / Claim /    │
 │ Decision / Outcome / Lesson  │
 └──────────────────────────────┘
                ↓
      Bounded Tools / Connectors
                ↓
 Privacy / Evals / Audit / Human Authority
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

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

## Safety posture

Before using the code, read:

- [`SECURITY.md`](SECURITY.md)
- [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`GOVERNANCE.md`](GOVERNANCE.md)
- [`EVALS.md`](EVALS.md)
- [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md)

Do not expose the local Core directly to the public Internet.

## Development philosophy: Safety-Limited Velocity

The project intentionally does **not** optimize for maximum capability growth.

Low-risk, local, reversible improvements can move quickly. Changes that increase external authority, irreversibility, privacy exposure, or high-stakes impact should move more slowly and require stronger evidence, rollback, observation time, and explicit governance.

See [`GOVERNANCE.md`](GOVERNANCE.md).

## Roadmap

The next evidence gap is less about adding more architecture and more about **real-world alpha validation**:

1. real-device macOS / Windows / Chrome testing
2. live provider E2E for optional OpenAI / Google paths
3. personal 30-day alpha with cognitive-agency metrics
4. failure-driven refinement
5. staged mobile capture / approval UX
6. only then consider narrowly bounded external actions

See [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Contributing

Contributions are welcome at the **Developer Alpha** level, especially around tests, threat modeling, documentation, reproducibility, privacy boundaries, and failure cases.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing a capability or authority expansion.

## Security reports

Do not post secrets, patient data, credentials, or exploit details in a public issue. See [`SECURITY.md`](SECURITY.md) for the disclosure process.

## License

Intelligence OS is licensed under the Apache License 2.0.

See [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

**Current stage:** `v0.7.2-alpha` · Developer Alpha · verification-centered · local-first · bounded automation · safety-governed
