# Useful Automation — v0.7.2-alpha

The automation goal is not maximum autonomy. It is **maximum useful automation within human authority**.

## Current execution boundary
### Auto-executable now
- `create_local_note`: local-only, private, reversible. It creates a Memory and supports Undo.

### Proposal-only now
- Gmail draft
- Calendar event/change
- Drive artifact
- Email send
- External publish/delete
- Permission change

Proposal-only actions can create an Approval record but **do not execute an external write in v0.7.2-alpha**.

## Invariant
Reasoning quality never grants authority. External side effects require a separate execution policy and, where consequential, explicit human approval.
