# Call for Review — Intelligence OS

Intelligence OS is a **Developer Alpha** and an **experimental** project. It is **not production-ready**, **not independently security-audited**, and its real-device validation and provider E2E validation are incomplete.

We are not only looking for approval. We are looking for failure modes.

## Review areas

Please review and report findings about:

- Architecture
- Privacy
- Security
- Verification
- Evals
- Red Team
- Human Cognitive Agency
- Bounded Automation
- Outcome Learning
- Native Messaging
- macOS / Windows compatibility
- UX / Accessibility

## What useful review looks like

Reproducible failures, unsafe assumptions, missing evidence, privacy-boundary regressions, authority-bypass cases, prompt-injection cases, verification gaps, portability problems, and documentation ambiguities are all valuable. Criticism is welcome; finding a failure mode is a contribution.

Use synthetic or non-sensitive data. Security-sensitive reports must follow [`SECURITY.md`](SECURITY.md); do not include secrets, credentials, private logs, exploit details, or other sensitive data in public issues.

## Current limitations

- Developer Alpha only
- Experimental and not production-ready
- No independent security audit
- Real-device macOS / Windows validation incomplete
- Chrome / Edge Native Messaging validation incomplete
- Provider end-to-end validation incomplete
- Passing tests and evals do not establish real-world safety

Reviews must preserve human authority, privacy boundaries, verification requirements, rollback capability, and Safety-Limited Velocity. No review request authorizes runtime authority expansion.
