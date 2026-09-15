# Architecture — Intelligence OS v0.7.2-alpha

## Layers

### Experience
Desktop Console, Browser Extension, future Mobile.

### Cognitive Kernel
Attention, Context, Executive, Skills, Reasoning, Verification.

### Knowledge
Memory, Provenance, Claims, Evidence, Contradictions, Corrections, Supersession.

### Action
Tools / connectors / future MCP actions. Consequential side effects are not silently executed.

### Governance
Privacy, permission boundaries, Evals, audit, Human Approval.

## Local-first data path

```text
Browser / Desktop
      ↓
Local Core
      ↓
SQLite Memory + Knowledge Lifecycle
      ↓
Optional external models only through privacy policy
```

## Verification path

```text
Claim
 ↓
Retrieve candidate local sources
 ↓
Classify evidence stance
 ↓
Score directness + source metadata + freshness
 ↓
Verified / Supported / Unverified / Contested / Contradicted
 ↓
Human correction or supersession when necessary
```

The scoring is intentionally conservative and method-labeled. The current alpha can add fetched public Web evidence through the Research path, but `verified` remains an evidence-policy status rather than a claim of absolute or global truth.

## v0.5-beta current-source path

```text
Executive
  ↓ research needed
Research Permission / Cost Gate
  ↓
Research Provider (OpenAI Web Search optional)
  ↓
Candidate URLs
  ↓
Public Fetch Boundary (SSRF/redirect/size checks)
  ↓
Memory + Provenance
  ↓
Retrieval / Reasoning
  ↓
Claim Verification / Contradiction
  ↓
Citation-ready Evidence
```

The Research Provider is replaceable. The Knowledge Lifecycle does not depend on OpenAI-specific source objects after source discovery: fetched Sources become normal local Memories with Provenance.
