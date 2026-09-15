# Intelligence OS v0.7.2-alpha — Release Notes

## Theme

**From Custom Instructions to a Reproducible Quality Harness**

This release promotes quality principles that were previously expressed mainly through custom instructions into explicit system layers.

## Added

- always-on Base Policy
- Adaptive Eval Profiles: `Light`, `Standard`, `Deep`, `High-Stakes`
- explicit separation of Base Policy, Orchestration, Evaluation, Verification, and Correction
- Quality Harness documentation
- project-lineage documentation from Prompt / Custom Instructions → Context Engineering → Harness Engineering → Intelligence OS
- Executive Plan now exposes `eval_profile`
- high-stakes health/legal paths automatically require stronger evidence handling and Verification
- Light tasks skip unnecessary external judging by default
- Deep/High-Stakes fallback clearly reports when only local heuristic evaluation is available

## Quality principle

Adaptive Evals change **evaluation effort**, not the minimum safety or anti-fabrication standard.

A Light task is cheaper to evaluate, but it may not invent facts. A High-Stakes task requires stronger evidence, counterevidence checks, and explicit human judgment.

## Release-point evidence

- Unit / regression tests: 80 / 80 PASS before final release build
- Executive / Adaptive-Evals benchmark: 11 / 11 PASS
- Verification benchmark: 6 / 6 PASS
- existing Red Team / Governance / scenario suites retained

Final public-release counts should be read from the release build output because the build pipeline is authoritative.

## Still Developer Alpha

The release remains unsuitable for identifiable patient data, clinical production, unrestricted external actions, or autonomous high-stakes decision making.
