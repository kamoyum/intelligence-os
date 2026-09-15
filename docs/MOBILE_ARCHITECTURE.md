# Mobile / iPhone Architecture — deliberately thin client

The mobile layer should **not** become a second autonomous Core.

## Mobile responsibilities
- quick capture (text / URL / photo metadata / voice transcript)
- Ask/Search against the trusted Core
- Unified Attention Queue
- approval inbox
- Outcome follow-up
- cognitive-agency feedback

## Mobile non-responsibilities
- unrestricted long-running autonomous research
- silent external writes
- credential-heavy administration
- independent permission expansion
- background agent loops that bypass Core governance

## Safety-limited rollout
1. Read-only capture/search prototype
2. Approval inbox
3. Outcome follow-up
4. Only after live evidence: bounded connector actions

Each stage must pass its own capability gate before the next stage is enabled.
