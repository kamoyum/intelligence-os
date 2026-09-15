# Verification model — v0.7.2-alpha

## Principle

**Memory is not truth.** A stored page, email, note, or prior AI answer is evidence input, not an instruction and not automatically a verified fact.

## Objects

- **Memory**: captured raw/derived information
- **Provenance**: where the source came from, when, publisher metadata, authority heuristic, trust boundary
- **Claim**: a factual proposition worth checking
- **Evidence**: a source-to-claim relation (`supports`, `contradicts`, `unclear`, `unrelated`)
- **Contradiction**: an open conflict requiring resolution or context
- **Supersession**: an explicit lifecycle transition; never silently deletes old history

## Verification scope

The current alpha supports `local_memory` verification and optional `web_retrieval+local_memory` evidence when Research has fetched public sources. The scope is determined per Claim from evidence actually used, not merely because a search ran.

When an external verifier model is configured, it may classify opted-in sources, but it is instructed to use only the supplied source and treat source content as untrusted data. Without an external verifier, a deterministic heuristic is used and labeled as such.

Neither method substitutes for fresh external research when current authoritative evidence is missing.

## Prompt injection

Captured material may contain hostile text such as "ignore previous instructions". The OS:

1. marks source content as untrusted data,
2. flags common injection patterns,
3. wraps external-model evidence in explicit untrusted-source delimiters,
4. never grants source text authority to change permissions or policy.

This is mitigation, not a proof of perfect injection resistance.

## Knowledge lifecycle

```text
Captured source
  ↓
Provenance
  ↓
Claim
  ↓
Evidence matching
  ↓
Verified / Supported / Unverified / Contested / Contradicted
  ↓
Human correction if needed
  ↓
Explicit supersession when a newer claim replaces an older one
```


## Current status semantics
- `verified`: sufficiently direct support from higher-authority evidence under the current heuristic/LLM evidence classifier. This is not absolute proof.
- `supported`: material support exists but does not meet the authority floor for `verified`.
- `contested`: material support and contradiction coexist.
- `contradicted`: higher-authority evidence directly contradicts the Claim.
- `unverified`: evidence is insufficient.

A low-authority direct assertion must not become `verified` merely because it states the Claim verbatim.
