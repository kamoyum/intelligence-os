# Roadmap — Intelligence OS

This roadmap describes **capability growth of the OS**, not feature count.

## v0.1 — Concept loop
Status: historical
- local capture
- memory
- simple retrieval
- mock reasoning

## v0.2 / v0.2.1 — Trusted local memory
Status: implemented
- token auth / constrained CORS
- FTS5 + optional semantic rerank
- privacy boundary: Memory != External LLM Context
- LLM/heuristic eval labeling
- audit log
- Google read-only connector foundation
- packaging/test hardening

## v0.3-alpha — Desktop runtime
Status: implemented
- Desktop lifecycle
- Native Messaging bridge
- browser extension as sensor/interface
- localhost fallback
- fixed extension identity

## v0.4-alpha — Cognitive Orchestration & Skills
Status: implemented
- Intelligence OS Manifest
- Executive task classification
- Auto / Augment / Human-control policy
- Skills registry/contracts
- human cognitive role surfaced per task
- browser bridge endpoint allowlist

## v0.5-alpha — Verification-centered local Knowledge Lifecycle
Status: implemented
- provenance
- stable Claim identity/history
- Evidence supports/contradicts/unclear
- contradiction records
- human correction and supersession
- local prompt-injection risk flags
- deterministic lifecycle simulation

## v0.5-beta — Current-source Research Path
Status: implemented in this release
- OpenAI Web Search provider adapter (optional)
- current-source discovery
- official/primary-source preference hints
- safe public URL fetching + redirect checks
- HTML/text/PDF source ingestion
- research run history
- daily web-search ceiling
- automatic low/medium-risk research routing
- explicit high-risk research permission
- web-retrieval + local-memory verification scope
- citation-ready source/evidence output
- deterministic and HTTP-level simulations

### Still incomplete before v0.6
- stronger domain-specific evidence grading (e.g. clinical study design hierarchy)
- production egress sandbox / robust DNS-rebinding defense
- richer correction/citation UI
- provider diversity / fallback research adapters
- evaluation of live-web research precision/recall on a benchmark set

## v0.6-alpha — Outcome Learning
Status: implemented in this release
- expectation / prediction capture
- decision links
- outcome capture
- transparent outcome-mismatch and surprise metrics
- Reflection Skill mechanism
- proposed lesson / rule update
- explicit human acceptance/rejection
- accepted lessons promoted to local private Memory
- learning status metrics
- deterministic and HTTP simulations

### Still incomplete before v0.7
- repeated-outcome aggregation before generalization
- domain-specific outcome metrics
- probabilistic scoring beyond the simple alpha mismatch/surprise metrics
- richer human reflection UI
- outcome source connectors / automatic outcome detection

## v0.6.2-alpha — Cognitive Guardrails & Kernel Polish
Status: implemented
- Goal-aware Attention driven by human Goals
- Executive evidence requirement + human checkpoint
- Query Safety across Web Research, remote reasoning, LLM Eval/Verification and embedding queries
- secret redaction-required policy
- due/overdue Outcome surfacing
- source-class split and vendor normative-claim authority cap
- common publication-date metadata extraction
- Skill maturity/executor transparency
- preflight + release verification pipeline
- Executive/Verification behavioral benchmark

## v0.6.3-alpha — Cognitive Resilience, Observability & Alpha Evals
Status: implemented
- unified Attention Queue across Goals / Knowledge conflicts / approvals / Outcome follow-up / Memory
- human cognitive mode: offload / collaborate / human_lead
- human-first prompt for high-value reasoning tasks
- Skill execution log and OS-level operational Evals
- cognitive-agency feedback signals, including “made me think less” warning
- injection-bearing Memory withheld from external reasoning/judging
- dedicated Red Team benchmark
- Alpha test protocol and threat model

## v0.7-alpha — Useful Automation
Status: partially implemented
- Action policy wired to a bounded Action Runtime
- local reversible `create_local_note` executes automatically and supports Undo
- Gmail draft / Calendar / Drive actions are proposal-only (no external write executor yet)
- send / publish / delete / permission change never auto-execute
- Approval records are created for external/consequential proposals
- Action runs are observable in System Evals

### Still incomplete before v0.7-beta
- live connector write adapters
- provider-specific rollback semantics
- signed real-device E2E
- external action audit/receipt verification


## v0.7.1-alpha — Safety-Limited Development Governance
Status: implemented
- explicit capability gate: HOLD / CONTAINED_ALPHA / ELIGIBLE_FOR_BOUNDED_EXPANSION
- freeze on privacy or safety-benchmark regression
- one-new-authority-boundary-per-release default
- external-write observation window + real-world evidence requirement
- irreversible autonomy blocked
- development-governance benchmark in release pipeline
- staged thin-client mobile architecture

### Principle
Capability can improve faster than authority. **Authority expansion waits for evidence.**

## v0.7.2-alpha — Quality Harness / Adaptive Evals
Status: implemented
- custom-instruction quality principles promoted into an always-on Base Policy
- Adaptive Eval Profiles: Light / Standard / Deep / High-Stakes
- Executive Plan exposes eval intensity and evidence expectations
- high-stakes tasks route toward stronger Research / Verification while external access remains permission-gated
- evaluation explicitly separated from evidence-based Verification
- benchmark cases added for ordinary comparison, financial-rule decisions, and postoperative health questions

### Principle
A shorter or cheaper evaluation path may never lower the Base Policy. **Evaluation effort is adaptive; the quality floor is not.**

## v0.8 — Ambient & Mobile
Planned
- iOS/mobile capture
- approval inbox
- goal-aware salience
- event-driven triggers
- background brief/consolidation
- interruption budget

## 1.0 — Personal Cognitive Infrastructure
Release criteria are longitudinal, not cosmetic:
- less repeated context work
- improved retrieval usefulness
- lower unsupported-claim rate
- faster time to trusted next action
- preserved human cognitive agency
- no unacceptable privacy/permission regression
- measurable learning from outcomes
