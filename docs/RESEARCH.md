# Current-source Research

> Introduced in v0.5-beta. Current project version: v0.7.2-alpha.

## Design rule

Search results are discovery signals, not truth.

The pipeline is:

`Query → Search → Candidate Source → Safe Fetch → Provenance → Local Evidence → Verification → Citation`

The research provider never gets unrestricted access to the full local Memory store. The default automatic path sends the current user query/claim only. Previously stored private Memory remains behind the existing external-LLM privacy gate.

## Automation boundary

- Low/medium-risk current/evidence tasks: external web research may run automatically when `INTELLIGENCE_RESEARCH_MODE=auto_public`.
- High/critical-risk tasks: external web research is withheld unless `allow_external_research=true` is explicitly supplied for that request.
- External real-world actions are separate and remain governed by the Action/Human Approval policy.

## Cost boundary

`INTELLIGENCE_WEB_SEARCH_DAILY_QUERIES` limits web-search calls per UTC day. When the ceiling is reached, the system returns an explicit unavailable state and continues with local evidence only; it does not silently invent current evidence.

## Source preference

The adapter prefers official/primary-looking domains and original research sources using a heuristic authority hint. This is metadata for ranking, not proof of reliability.

## Web evidence is untrusted

Fetched pages are treated as evidence text, never as instructions. Known prompt-injection patterns are flagged. External LLM classifiers wrap source content as untrusted source data and are instructed not to follow webpage instructions.

## Fetch security

The reference fetcher:
- accepts only HTTP/HTTPS,
- rejects localhost/private/link-local/reserved addresses,
- validates redirect targets,
- caps response bytes,
- parses text/HTML and bounded PDFs.

Known limitation: DNS validation and the HTTP client perform separate resolution steps, so sophisticated DNS-rebinding/TOCTOU attacks are not considered fully mitigated. Production deployment should use an egress proxy or network sandbox with explicit public-network policy.

## Verification semantics

- `local_memory`: evaluated only against locally stored sources.
- `web_retrieval+local_memory`: web sources actually contributed evidence to that Claim. This means they were retrieved now; it does not assert that the underlying publication itself is newly published.

Neither scope is equivalent to mathematical proof or professional authority.
