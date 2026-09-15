# Alpha Test Protocol — Intelligence OS

## Why test
The central hypothesis is not “the AI can answer questions.” It is:

> Intelligence OS can move repetitive cognitive work away from the human while preserving or improving high-value human thinking, verification, continuity and control.

## 30-day alpha questions
1. Did the OS reduce repeated explanation or repeated research?
2. Did retrieved Memory help more often than it distracted?
3. Did Verification catch stale, weak or conflicting knowledge?
4. Did Human-first prompts preserve judgment on high-value tasks?
5. Did automation remove mechanical work without crossing authority boundaries?
6. Did Outcome Learning produce lessons that the human actually accepted and reused?

## Minimum metrics
### Continuity
- Ask tasks with at least one reused Memory / total Ask tasks
- Duplicate investigation avoided (manual user mark)
- “I already told the AI this” events

### Verification
- claims verified / supported / unverified / contested
- contradictions surfaced
- corrections / supersessions confirmed by human
- research failures where the OS refused to guess

### Cognitive agency
- AUTO / COLLABORATE / HUMAN_LEAD task counts
- human-first prompt shown count
- user override count
- decisions where human criterion changed after evidence

### Automation value
- minutes of mechanical work estimated saved (user-entered estimate initially)
- approval requests generated / approved / rejected
- accidental or unwanted autonomous side effects: target = 0

### Learning
- expectations with outcomes collected
- overdue outcomes
- proposed lessons / accepted lessons / rejected lessons
- later reuse of accepted lesson Memory


### Development pacing
- authority boundaries added per release (target: <= 1)
- releases held because of safety/privacy regressions
- contained capabilities promoted only after observation evidence
- incidents discovered before vs after authority expansion
- capability improvements that did **not** receive additional authority

## Qualitative diary (10 seconds per notable use)
Mark one:
- `helped me think`
- `saved repetitive work`
- `caught an error`
- `too much noise`
- `made me think less`
- `wrong / unsafe`

The product fails its North Star if “made me think less” rises on high-value tasks even while task completion gets faster.

## Alpha safety scope
Allowed: public web, synthetic data, personal non-sensitive notes.
Avoid: patient-identifiable data, hospital confidential data, unrestricted financial credentials, production external actions.
