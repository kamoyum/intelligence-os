# Security Policy

## Project status

Intelligence OS is a **Developer Alpha**. It is not a production security boundary and is not approved for identifiable patient data, workplace secrets, regulated production data, or autonomous high-stakes decision making.

The reference Core binds to `127.0.0.1`. **Do not expose the local API directly to a LAN or the public Internet.**

## Supported version

Security fixes currently target the latest `0.7.x-alpha` source tree only.

## Reporting a vulnerability

Please **do not** open a public issue containing:

- API keys, passwords, tokens, OAuth credentials
- personal or patient information
- exploit payloads that enable immediate compromise
- private logs or databases

Preferred reporting path:

1. Use GitHub **Private Vulnerability Reporting** if it is enabled for the repository.
2. If private reporting is not yet enabled, open a minimal public issue titled `Security: private disclosure requested` **without exploit details or sensitive data**, so the maintainer can establish a private channel.

Until a private disclosure channel is configured, do not publish weaponizable details.

## Core security invariants

- **Capability ≠ authority.** More model capability does not grant more tool permission.
- **Memory ≠ external permission.** Local storage does not imply permission to send content to a remote model.
- **External content is untrusted data.** Web/email/document content must not become policy or system instruction.
- **High-risk external changes require human authority.**
- **Secrets are blocked from external reasoning, Web Research, remote evals, and embeddings until redacted.**
- **No silent permission expansion.**

## Current controls

- random local bearer token
- authenticated API endpoints
- loopback binding
- TrustedHost restrictions
- narrow CORS model
- Native Messaging route allowlist
- ignored local token/OAuth/database files
- Query Safety gate
- Memory external-sharing policy
- research URL validation and size ceilings
- audit / approval / action-run records
- Red Team behavioral benchmark
- release archive hygiene checks

## Important residual risks

This alpha is **not** hardened against:

- local malware with user-level filesystem access
- a fully compromised browser profile
- sophisticated DNS rebinding / TOCTOU against the alpha Web fetcher
- multi-user / multi-tenant deployments
- enterprise identity / key management requirements
- all prompt-injection strategies
- malicious model-provider behavior
- supply-chain compromise
- unsigned desktop distribution risk

The local SQLite database is not encrypted at rest by the application itself.

## Prompt injection

Prompt-injection detection is a **secondary signal**, not a complete defense. The primary boundary is architectural: retrieved content is treated as untrusted evidence/context, not as instruction authority.

## External providers

Optional OpenAI / Google integrations can transmit data outside the local machine. Use only non-sensitive data during alpha testing and review `docs/DATA_BOUNDARIES.md` before enabling them.

## Production requirements not yet met

A production/cloud deployment would require, at minimum:

- managed identity and short-lived sessions
- TLS-only access
- encrypted secret storage / OS keychain integration
- encrypted storage and key management
- tenant isolation
- mature OAuth revocation / retention controls
- rate limiting and abuse controls
- isolated outbound fetch / egress policy
- signed/notarized installers
- security review and dependency/supply-chain controls
- real incident response process

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for the broader threat model.
