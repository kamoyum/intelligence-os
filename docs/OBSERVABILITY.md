# Observability & System Evals

v0.6.3-alpha adds OS-level observability.

## Skill Runs
`skill_runs` records which capability actually ran. A Skill contract in documentation is not counted as execution.

Tracked examples:
- Memory retrieval count
- Research run status and source count
- Verification claim count
- Assisted reasoning skills

API: `GET /api/skills/runs`

## System Evals
API: `GET /api/system/evals`

Current signals include:
- task completion rate
- Memory reuse rate
- Research success rate
- Lesson acceptance rate
- verified-claim share
- unresolved contradictions
- pending approvals
- skill execution counts

These are **operational signals**, not proof that Intelligence OS improves human cognition. Human-value outcomes require longitudinal alpha testing.

## Unified Attention Queue
API: `GET /api/attention/queue`

It combines:
- human Goals
- overdue Outcome follow-up
- unresolved Knowledge conflicts
- approval requests
- failed research
- relevant Memories

The queue is a prioritization surface, never an autonomous command queue.
