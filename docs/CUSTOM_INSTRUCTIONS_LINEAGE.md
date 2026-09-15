# From Custom Instructions to Intelligence OS

Intelligence OS grew out of an earlier attempt to improve AI quality through detailed custom instructions.

That work produced several durable lessons:

- anti-hallucination instructions are necessary but not sufficient
- the model should not simply agree with the user
- primary sources should be preferred when factual freshness matters
- conclusion strength should follow evidence strength
- verified, inferred, and unverified information should be distinguishable
- important decisions should include counterevidence and failure conditions
- errors should be corrected explicitly
- evaluation effort should scale with the task rather than treating every prompt equally

The key architectural realization was that these concerns belong to different layers.

## Evolution

```text
Prompt Engineering
      ↓
Custom Instructions / Base Policy
      ↓
Context Engineering
      ↓
Harness Engineering
      ↓
Adaptive Evals + Verification
      ↓
Intelligence OS
```

### Custom Instructions

Useful for persistent preferences and broad quality expectations.

Weakness: they are still instructions to a model and are difficult to measure directly.

### Context Engineering

Controls what information, Memory, evidence, tools, and constraints are available at the moment of reasoning.

### Harness Engineering

Controls routing, Skills, tool use, permissions, stop conditions, evaluation, and correction around the model.

### Intelligence OS

Adds continuity across time: Memory, Provenance, Outcomes, Learning, Governance, and Human Authority.

The result is intentionally not “a longer system prompt.” It is a move from **instruction quality** toward **system quality**.
