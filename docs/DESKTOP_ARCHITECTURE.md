# Desktop architecture

> Introduced in v0.6-alpha. Current project version: v0.7.2-alpha.

The Desktop runtime keeps the cognitive kernel independent from browser lifecycle.

```text
Browser Extension
  ↓
Native Messaging
  ↓
Allowlisted Native Host
  ↓
Local Core
```

The Native Host never exposes connector sync/OAuth/audit/permission-bearing routes to the browser extension. Legacy localhost/token transport is retained only as a development fallback.

Desktop is an execution surface, not the Intelligence OS philosophy itself. Future iOS, cloud workers and other clients should connect to the same Kernel contracts rather than reimplement cognition in each UI.
