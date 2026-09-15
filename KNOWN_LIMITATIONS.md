# Known Limitations

This document exists to make the alpha boundary explicit.

## Runtime / distribution

- no signed/notarized macOS or Windows installer
- source-distributed Python runtime
- real-device Chrome/Edge Native Messaging still requires broader testing
- no production auto-update channel

## Provider E2E

- optional OpenAI / Google paths require real user credentials and live-provider testing
- provider API behavior can change independently of this repository

## Security

- local SQLite is not application-encrypted at rest
- alpha Web fetch is not an enterprise egress sandbox
- prompt injection is mitigated, not solved
- local malware / compromised browser profiles remain out of scope
- no multi-tenant security design

## Verification

- source authority is heuristic and context-dependent
- evidence classification can be wrong
- publication dates are not always extractable
- `verified` is a policy state, not absolute truth
- contradictory evidence can remain unresolved until human review

## Executive / Skills / Adaptive Evals

- Executive routing is deterministic/benchmark-driven, not a general autonomous planner
- some Skills remain assisted rather than independent state machines
- the system can choose the wrong workflow
- Adaptive Eval tiers are deterministic heuristics and can over-escalate or under-escalate a task
- a Deep / High-Stakes profile does not guarantee that sufficient external evidence is available

## Outcome Learning

- outcomes and match scores remain partly human-entered
- the system does not independently observe all real-world outcomes
- lessons are contextual and may not generalize

## Automation

- useful automation is intentionally narrow
- external actions remain proposal-only in the current alpha
- the system is not a general-purpose autonomous agent

## High-stakes use

Do not use the current alpha as an autonomous medical, legal, financial, employment, safety-critical, or emergency decision system.
