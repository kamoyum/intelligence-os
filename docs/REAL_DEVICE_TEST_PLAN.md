# Real-Device Test Plan — next evidence gate

This is the next major evidence gap. Do **not** widen authority before it is completed.

## Stage 1 — Core only
- launch Core on the actual computer
- confirm loopback binding
- confirm token setup
- run capture / Ask / Verification / Outcome Learning
- verify restart persistence
- verify no unexpected external traffic in mock/local mode

## Stage 2 — Browser bridge
- load the exact packaged extension
- install Native Messaging host
- ping / health / capture / ask
- confirm blocked admin routes stay blocked
- restart browser and OS and repeat

## Stage 3 — OpenAI provider
Use non-sensitive synthetic queries first.
- enable one provider at a time
- confirm Query Safety prevents secret disclosure
- confirm daily caps
- confirm provider failure degrades explicitly
- compare cited sources with actual fetched evidence

## Stage 4 — Google read-only
Start in `safe` mode.
- OAuth connect
- Calendar read-only
- narrow Drive access
- confirm connector-derived Memory remains hard-local
- deliberately test logout/revocation/failure

Do not enable broader Gmail/Drive scopes until the read-only boundary is understood.

## Stage 5 — Longitudinal Alpha
Minimum recommended observation before any external-write executor: **14 days** plus real-world evidence.

Measure:
- usefulness
- cognitive-agency feedback
- privacy/security incidents
- unwanted alerts/noise
- verification failures
- rollback/restore behavior

## Stop conditions
Immediately HOLD capability expansion if any of the following appears:
- privacy regression
- unexplained external request
- authority boundary bypass
- critical Red Team regression
- irreversible unexpected side effect
- repeated “wrong / unsafe” user feedback
