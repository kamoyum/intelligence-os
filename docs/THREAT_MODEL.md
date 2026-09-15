# Threat Model — Intelligence OS v0.7.2-alpha

## Security objective
Intelligence OS is a local-first personal cognitive infrastructure. Security is not only confidentiality: the system must also prevent untrusted information from silently becoming authority, prevent AI reasoning from gaining real-world permissions, and keep the human in control of consequential actions.

## Assets
- Local Memory / personal context
- API credentials and OAuth tokens
- User goals, decisions, outcomes and accepted lessons
- Knowledge state (claims, provenance, corrections, supersession)
- Browser-to-Core authority boundary

## Trust zones
1. **Human authority** — goals, approvals, corrections, lesson acceptance.
2. **Local trusted Core** — storage, policy, retrieval, routing, audit.
3. **Local untrusted content** — captured webpages, email/doc text, imported sources.
4. **External models/search** — useful compute, never trusted with unrestricted local data.
5. **External web** — untrusted evidence discovery surface.
6. **Browser companion** — limited client; not an administrative authority surface.

## Primary threats and current controls
| Threat | Control | Residual risk |
|---|---|---|
| Secret/PII exfiltration in query | Query Safety; Secret blocks external calls; Sensitive requires explicit permission | Pattern detection is incomplete; users can still intentionally disclose data |
| Private Memory exfiltration | hard-local connector sources; sensitivity gate; opt-in external memory | Metadata and novel secret formats may evade classification |
| Prompt injection in Web/Memory | untrusted-data prompting; detection flag; injection-bearing memories withheld from external LLM judging/reasoning | Heuristics do not prove safety; model-level injection remains an active risk |
| SSRF from research fetch | public URL validation, private/loopback/link-local/reserved blocking, redirect validation, size/time caps | DNS rebinding and sophisticated network attacks need sandboxed fetch infrastructure for production |
| Low-quality source promoted to truth | provenance authority/directness thresholds; `supported` distinct from `verified` | Authority priors are heuristic and domain-level only |
| Stale page treated as current | publication time separated from retrieval time | Publication date extraction can fail or be wrong |
| Browser extension privilege escalation | Native Messaging route allowlist; fixed extension ID; token held by native host | A compromised trusted extension can still invoke allowed routes |
| Irreversible action by AI | action policy + approval layer; authority-bearing routes excluded from browser bridge | Future action connectors require separate per-action threat models |
| Memory accumulation becomes false knowledge | claims/evidence/contradiction/supersession lifecycle | Human correction and source quality still matter |
| AI “learning” bad rules from one outcome | lessons are proposed and require human acceptance | Humans can accept poor lessons; longer-horizon calibration is not implemented |
| Safety debt hidden by rapid feature growth | release capability gate; benchmark regression freeze; one authority boundary/release | Metrics can still miss novel failure modes; independent review remains necessary |

## Non-negotiable invariants
- Memory is not truth.
- Retrieval is not verification.
- Search is not verification.
- Model confidence is not evidence.
- External actions are not granted by reasoning quality.
- Global settings must not silently override hard-local data boundaries.
- High-risk decisions remain human-owned.
- Safety evidence must lead authority expansion.
- A faster release cadence is not a safety argument.

## Production blockers
Before consumer production use, add: signed installers, OS keychain/secure enclave integration, isolated network fetch worker, stronger identity/user separation, backup/restore and deletion guarantees, real-device E2E, connector-specific privacy reviews, and independent security review.
