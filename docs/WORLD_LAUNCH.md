# World Launch Plan — Intelligence OS

This document tracks how to make Intelligence OS discoverable without overstating what has been validated.

## Positioning

**Short category:** Governance-first Personal Cognitive Infrastructure

**One-line pitch:**  
Intelligence OS is a local-first cognitive layer for persistent memory, evidence-aware verification, outcome learning, and bounded automation that keeps consequential authority with the human.

**Plain-language pitch:**  
Your AI should remember useful context, verify claims, learn from outcomes, and automate repetitive work — without silently sending secrets, treating memory as truth, or taking over consequential decisions.

## What makes the project distinct

- Memory is useful context, not truth.
- Retrieval is not verification.
- Model confidence is not evidence.
- Capability does not automatically grant authority.
- `SAFE / SENSITIVE / SECRET` gates apply before optional external reasoning/search.
- Learning is tied to outcomes and explicit human acceptance.
- Automation is intended to be bounded, observable, and reversible where possible.
- Safety-Limited Velocity deliberately slows higher-risk capability/authority expansion.
- Human cognitive agency is treated as something to preserve and evaluate.

## Current evidence boundary

Public repository status:

- Developer Alpha
- experimental
- Apache-2.0
- not production-ready
- not independently security-audited
- real-device macOS / Windows validation incomplete
- provider end-to-end validation incomplete
- longitudinal personal-use validation incomplete

Passing tests, simulations, benchmarks, CI, or CodeQL does not establish real-world safety.

## Discovery checklist

### GitHub

Recommended repository topics:

- `personal-ai`
- `ai-agents`
- `local-first`
- `ai-safety`
- `context-engineering`
- `evals`
- `human-ai-collaboration`
- `knowledge-management`
- `python`

Also:

- keep the repository description outcome-oriented
- add a short demo when real-device setup is stable enough to reproduce
- create a tagged alpha release once the install path is verified on real devices
- use Issues for reproducible failure cases and real-device validation
- use Discussions for architecture, governance, and research questions

## Outreach order

1. GitHub search/discovery and existing AI/open-source contacts
2. HCI / human-AI collaboration / AI governance researchers
3. local-first and agent-evaluation communities
4. Hacker News once the project is easy enough for strangers to run
5. Reddit communities only when their current self-promotion rules are satisfied
6. accelerator / research / grant programs after initial real-world evidence exists

## Hacker News

Do **not** treat Hacker News as an advertising channel.

A Show HN should be something people can actually try. Before posting:

- verify a fresh install path on at least one real macOS or Windows machine
- make first-run instructions short and reproducible
- provide a concrete example people can test
- be available to answer technical questions yourself
- do not ask anyone to upvote or comment
- write the submission/comment in your own voice rather than posting generated promotional copy

Possible factual title direction after the try-it path is ready:

`Show HN: Intelligence OS – a local-first cognitive layer for memory, verification and bounded AI actions`

Talking points to rewrite personally:

- why repeated context loss in AI interactions bothered you
- why you separated memory from truth and capability from authority
- what is implemented versus only simulated or planned
- one concrete local workflow people can reproduce
- what kinds of failure reports you most want
- what you still do not know

## Reddit

### r/LocalLLaMA

Treat this as a community first, not a launch surface. Current moderation emphasizes meaningful participation and limits self-promotion. Participate in other technical discussions before posting your own project, disclose AI assistance when the rules require it, and write the actual post yourself.

When eligible, focus on technical questions rather than promotion:

- local/private memory boundaries
- model/provider independence
- evidence and verification architecture
- prompt-injection handling
- local-first tradeoffs
- human authority over agent actions

### r/selfhosted

Do not promote Intelligence OS there while it is still a Developer Alpha if current rules require promoted apps to be production-ready. Recheck the subreddit rules before posting.

## X / social short form

A concise message can center the design tension rather than claiming novelty:

> I’ve been building Intelligence OS, an experimental local-first Personal Cognitive Infrastructure.
>
> The core idea is simple:
> Memory ≠ truth.
> Retrieval ≠ verification.
> Capability ≠ authority.
>
> It connects persistent context, evidence-aware verification, outcome learning, and bounded automation while keeping consequential decisions human-controlled.
>
> Developer Alpha, Apache-2.0. Criticism and failure cases welcome.

Repository: https://github.com/kamoyum/intelligence-os

## Research / grant pitch

Lead with the research question rather than the software:

**Can persistent personal AI reduce repetitive cognitive work without reducing human cognitive agency or silently expanding AI authority?**

Potential study outcomes:

- duplicate research avoided
- time to trusted action
- correction frequency
- errors caught before action
- accepted/rejected learned lessons
- perceived cognitive offloading
- `helped_me_think`
- `saved_repetitive_work`
- `caught_an_error`
- `too_much_noise`
- `made_me_think_less`
- `wrong_or_unsafe`

## Next launch gate

Before a broad global push, complete:

1. real-device alpha on at least one macOS and one Windows environment
2. one reproducible end-to-end demo
3. one short screen recording or GIF showing the workflow
4. live-provider safe-mode validation where applicable
5. an initial longitudinal personal-use dataset
6. external failure-mode review

The goal is not maximum reach before evidence. The goal is to make the project easy to understand, easy to test, and easy to criticize constructively.
