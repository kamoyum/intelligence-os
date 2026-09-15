# Skills Layer

> Introduced in v0.5-alpha. Current project version: v0.7.2-alpha.

A Skill is not a persona and not merely a prompt. It is a reusable cognitive procedure with:

- purpose
- steps
- default automation level
- explicit human role
- verification requirement
- stop condition
- eval dimensions

The initial built-in Skills are:

| Skill | Default | Human role |
|---|---|---|
| Memory & Context | Auto | Correct stale/irrelevant context |
| Organize | Auto | Confirm meaning when structure matters |
| Research | Augment | Own question and interpretation |
| Verification | Augment | Decide evidence threshold |
| Decision Support | Augment | Own values and final decision |
| Reflection & Learning | Augment | Interpret outcome and lessons |
| Brief | Auto | Override system salience |

The Executive selects Skills per task. Skills are designed to remain model-agnostic and tool-agnostic.

Future Skills should be added only when they have a stable procedure, measurable value, explicit human/AI division of labor, and an eval contract.
