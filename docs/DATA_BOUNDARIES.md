# Data Boundaries — Intelligence OS v0.7.2-alpha

## Principle
Local memory and external model context are different security domains. Storing data in Intelligence OS does **not** imply consent to transmit it to an external LLM or embedding provider.

## Defaults
- `INTELLIGENCE_EXTERNAL_LLM_MODE=opt_in`
- New browser captures: external sharing is OFF unless the extension option is explicitly enabled.
- Google Calendar / Drive / Gmail sync: external sharing is hard-local in the current alpha; global `all` mode does not override this connector boundary.
- Embeddings obey the same external-sharing policy.
- `off`: no Memory is sent to external LLM/embedding services. The user query can still be sent when a remote reasoning model is configured.
- `opt_in`: only Memory rows with `allow_external_llm=1` may be transmitted.
- `all`: all otherwise-eligible retrieved Memory may be transmitted, but hard-local connector data and `sensitive`/`highly_sensitive` Memory remain blocked. Not recommended for normal use.

## Current query boundary
The text typed into the Ask box is itself data. Before external reasoning, Web Research, remote evaluation/verification, or embeddings, the current alpha applies the shared Query Safety policy.

- `safe`: may use configured external providers.
- `sensitive`: requires explicit per-request permission before external transmission.
- `secret`: external transmission is blocked until the query is redacted or rephrased.

This is defense-in-depth, not a claim of perfect PII/secret detection.

## Embedding cost guardrail
`INTELLIGENCE_EMBEDDING_DAILY_INPUTS` sets a hard daily ceiling on embedding inputs. FTS5 remains available when the budget is exhausted or the embedding call fails.

## Google data
Broad Gmail/Drive scopes can be Restricted Google OAuth scopes. Public distribution may require verification and, if restricted data is stored or transmitted through servers, a security assessment. Keep broad scopes private/test-only until those requirements are satisfied.


## Browser page context
The Side Panel does not automatically attach the current page title or URL to an Ask request unless the browser-capture external-sharing option is enabled. This closes a subtle path where a sensitive page could otherwise be disclosed even when its stored Memory was withheld.


## Current-source research boundary (v0.5-beta)
- Automatic web research sends the current query/claim to the configured research provider; it does not automatically attach private stored Memory.
- Low/medium-risk evidence/current tasks may research automatically when research mode is enabled and daily cost limits allow it.
- High/critical-risk queries require explicit per-request permission because query text itself may contain sensitive information.
- Fetched public web sources are stored as `sensitivity=public` and `allow_external_llm=1`; they remain untrusted evidence and may contain prompt injection.
- Failed/unfetched URLs are not inserted as direct evidence.
- Research results and fetched sources are auditable through `research_runs` and Provenance records.

## Query Safety boundary (v0.7.2-alpha)
The text of a query is itself data. The Core classifies queries as `safe`, `sensitive`, or `secret`.
- `safe`: external reasoning/research may be used when configured.
- `sensitive`: requires explicit per-request permission before external reasoning/research.
- `secret`: external research/reasoning/verification/embedding transmission is blocked until redacted/rephrased.
This is defense-in-depth, not a claim of perfect PII/secret detection.
