# v0.1 External Review → v0.2 Response

The v0.1 review identified five concrete debts. v0.2 treats them as engineering requirements rather than cosmetic feedback.

## 1. Retrieval scaling

**v0.1:** up to 300 SQLite rows loaded and scored in Python.

**v0.2:** SQLite FTS5 provides bounded candidates. Optional embeddings rerank only the leading candidates. No unbounded full-memory loop is required for normal retrieval.

## 2. Evals were not true verification

**v0.1:** deterministic keyword heuristics were labeled as Evals.

**v0.2:** the response reports the eval method explicitly. If a model is configured, an independent evaluator judges support against the supplied context; otherwise the system says `heuristic` and explicitly states it is not a fact-check.

A future Research Eval path is still needed for external claim verification.

## 3. API authentication / permissive CORS

**v0.1:** localhost API had no auth and wildcard CORS.

**v0.2:** bearer token authentication is mandatory for functional APIs. CORS is narrowed. The extension stores the local token in Chrome local storage. The Console receives the local token only from the local Core.

## 4. Generated DB/cache in the archive

**v0.1:** prototype DB and Python cache were accidentally packaged.

**v0.2:** packaging excludes databases, local tokens, OAuth tokens, caches and secrets. `.gitignore` reflects the same policy.

## 5. No automated tests

**v0.1:** none.

**v0.2:** tests cover Japanese/ASCII tokenization, FTS retrieval, source-key upsert, DB/FTS initialization, summary bounds, heuristic eval labeling and token persistence.


## v0.2.1 follow-up
The second external review identified three remaining hardening items. v0.2.1 addresses them before adding v0.3 features:
1. Console token exposure: removed token injection from Console HTML; loopback-only setup display.
2. External LLM privacy boundary: Memory now carries `allow_external_llm`; Google-derived Memory defaults to false; remote reasoning/evals/embeddings filter on this boundary.
3. Embedding cost guardrail: added UTC daily input ceiling with persisted usage accounting and FTS fallback.

Additional hardening: Chrome `storage.local` is restricted to trusted extension contexts.
