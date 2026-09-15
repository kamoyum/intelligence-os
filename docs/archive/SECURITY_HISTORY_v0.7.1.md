# Security and Governance

## Security boundary

v0.7.1-alpha is a local experimental prototype and binds to `127.0.0.1`. It must not be exposed directly to the public Internet.

## Controls added in v0.2

- random bearer token generated locally
- API endpoints reject missing/invalid token
- token stored outside version-controlled files
- CORS limited to local Console origins and Chrome-extension origins
- browser permissions kept narrow
- Google credentials stored in ignored local data files
- audit log for captures, tasks, approvals and connector syncs
- explicit approval records
- restricted Google mode disabled by default

## Threat model

Protect against:

- arbitrary web pages attempting localhost API calls
- accidental publication of DBs/tokens/OAuth credentials
- over-broad OAuth permissions
- prompt content being treated as instructions to expand permissions
- high-risk external actions without user consent
- false confidence from evaluator scores

Not yet production-grade against:

- local malware with user-level filesystem access
- multi-user/multi-tenant attacks
- token theft from a compromised browser profile
- sophisticated connector exfiltration
- encrypted-at-rest requirements

## Human approval invariant

An AI-generated proposal is not authority.

High-risk actions must go through:

```text
Proposal → Risk classification → Human approval → Tool execution → Outcome audit
```

Self-permission escalation is prohibited.

## Production requirements before cloud deployment

- managed identity and short-lived sessions
- TLS-only access
- encrypted secrets manager
- tenant isolation
- encrypted database / key management
- CSRF/state protections for OAuth and browser sessions
- rate limits
- structured audit events
- connector-specific scopes
- revocation UI
- data retention controls
- incident logging
- security review and Google verification where applicable


## v0.2.1 hardening
- The Console no longer embeds the API token in returned HTML. The user enters it per browser tab/session.
- `/setup` displays the bootstrap token only when `INTELLIGENCE_CORE_ORIGIN` resolves to loopback (`127.0.0.1`, `localhost`, or `::1`).
- The reference launcher binds Uvicorn to `127.0.0.1`. **Do not change the bind address to `0.0.0.0` or expose port 8765 to a LAN/Internet.** A cloud deployment requires a different authentication/TLS/multi-user design.
- Extension local storage access is restricted to trusted extension contexts.
- Memory has an explicit external-LLM sharing flag. Google-synced data defaults to no external sharing.
- Embeddings use the same sharing policy and a daily input ceiling.

See `DATA_BOUNDARIES.md` before enabling any remote model.

- TrustedHostMiddleware restricts Host headers to loopback names, reducing local-service DNS-rebinding exposure.
- Side Panel does not append the current page title/URL to a remote-model query unless the same explicit external-sharing option is enabled.

## v0.3 Desktop / Native Messaging boundary

The browser extension prefers Chrome/Edge Native Messaging. The native host is deliberately a thin bridge and does not contain the long-term Memory or reasoning logic.

- Extension ID is stabilized with a public manifest key so the native host can allow exactly one extension origin.
- The bridge only accepts GET/POST requests to paths beginning with `/`; traversal-style paths are rejected.
- The bridge reads the local Core token from the local data directory and never returns that token to the extension.
- Core still binds to loopback only and retains token / TrustedHost protections.
- The legacy HTTP path remains as a beta fallback and therefore must keep its token private.
- Moving the source directory after native-host installation requires reinstalling the bridge because the manifest points to the installed launcher/source path.

### Not yet production hardened

- The Desktop launcher is a source-distributed Python beta, not a signed/notarized Windows/macOS package.
- Windows Native Messaging source installation builds a local executable with PyInstaller; code signing is not yet included.
- The Desktop GUI does not yet use OS-native keychain storage for API credentials; the API key field is session-only by default.
- Multi-user OS accounts, MDM deployment, enterprise policy enforcement, remote administration, and signed auto-updates are out of scope for v0.3.

## v0.5-alpha cognitive/authority and evidence boundary

v0.5-alpha separates **cognitive automation**, **evidence authority**, and **authority to change the world**.

- Executive `auto` does not imply unrestricted external execution.
- High-value cognition defaults to `augment` even when technically automatable.
- High/critical risk remains human-controlled or approval-gated.
- The browser Native Messaging host now uses an explicit route allowlist. Connector sync, OAuth, audit and approval mutation routes are not callable through the browser bridge.
- Skills declare the human role and stop condition so automation boundaries are inspectable rather than implicit.
- Captured source text is treated as untrusted data, not as policy or system instructions.
- Verification records prompt-injection risk indicators and wraps opted-in evidence with untrusted-source delimiters before external classification.
- Claim supersession is explicit and human-confirmed rather than silently rewriting old knowledge.
- `verified` is scoped to the currently stored evidence; it is not a guarantee of external-world truth.

Remaining important gaps include live authoritative-source discovery, stronger prompt-injection isolation/sandboxing, signed distribution, secure OS credential storage, multi-user isolation and production-grade cloud authentication.


## v0.5-beta web-research boundary
- Web research is read-only but has privacy and cost consequences. Automatic research is limited to low/medium-risk queries; high/critical-risk queries require explicit per-request opt-in.
- Public URL fetching blocks loopback/private/link-local/reserved addresses, validates each redirect target, and caps response size.
- Research Source text is untrusted data and is never granted tool/policy authority.
- Unfetched search results are not promoted to direct Evidence.
- Search calls have a daily ceiling. Provider/network failures are surfaced explicitly; current evidence is never fabricated as a fallback.
- Known gap: DNS validation is not a production egress sandbox. A hardened release should use an isolated network fetch service / egress proxy.

## v0.6-alpha learning boundary
- Outcome Learning mutates local Memory only after explicit human acceptance of a proposed lesson.
- Rejected/proposed lessons do not become reusable Memory.
- Learning records are personal/contextual evidence and must not be automatically reclassified as external objective truth.
- The alpha match score is human-entered; it is not a clinical/statistical outcome validator.


### Residual web-fetch risks
- URL validation blocks loopback/private/link-local/reserved destinations and manually validates redirects.
- Response bytes are streamed with a hard size ceiling.
- DNS is resolved before fetch, but the current Python/httpx adapter does not pin the validated IP through the TLS connection; sophisticated DNS-rebinding/TOCTOU attacks remain a residual risk. Do not treat this alpha fetcher as a hardened enterprise SSRF sandbox.
- Query text sent to the research provider is protected only by the Executive risk gate and explicit high-risk permission; there is not yet a complete PII/secret detector.
