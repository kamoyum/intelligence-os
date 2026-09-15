from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class SkillSpec:
    id: str
    name: str
    purpose: str
    default_automation: str
    human_role: str
    requires_verification: bool
    steps: tuple[str, ...]
    stop_condition: str
    eval_dimensions: tuple[str, ...]
    maturity: str = "contract"  # executable | assisted | contract
    executor: str | None = None

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("steps", "eval_dimensions"):
            data[key] = list(data[key])
        return data


SKILLS: dict[str, SkillSpec] = {
    "memory_context": SkillSpec(
        id="memory_context",
        name="Memory & Context",
        purpose="Retrieve only the past context that is relevant to the current goal.",
        default_automation="auto",
        human_role="Correct or reject retrieved context when it is stale, irrelevant, or wrong.",
        requires_verification=False,
        steps=("identify current goal", "retrieve candidate memories", "rank relevance", "build a small working context"),
        stop_condition="Enough context is available to proceed without flooding the working context.",
        eval_dimensions=("relevance", "precision", "staleness"),
        maturity="executable", executor="retrieval.retrieve_memories",
    ),
    "organize": SkillSpec(
        id="organize",
        name="Organize",
        purpose="Reduce low-value cognitive load by structuring, extracting, deduplicating, and formatting information.",
        default_automation="auto",
        human_role="Define the intended use when structure changes meaning.",
        requires_verification=False,
        steps=("extract", "deduplicate", "group", "format"),
        stop_condition="Information is easier to use without changing its meaning.",
        eval_dimensions=("completeness", "faithfulness", "clarity"),
        maturity="assisted", executor="reasoning+local formatting",
    ),
    "research": SkillSpec(
        id="research",
        name="Research",
        purpose="Identify what is unknown and gather evidence needed to answer it.",
        default_automation="augment",
        human_role="Own the question, relevance criteria, and interpretation of the evidence.",
        requires_verification=True,
        steps=("decompose question", "identify evidence needs", "search sources", "compare evidence", "surface uncertainty"),
        stop_condition="The evidence is sufficient for the decision, or remaining uncertainty is explicit.",
        eval_dimensions=("source_quality", "coverage", "recency", "directness"),
        maturity="executable", executor="research.run_web_research",
    ),
    "verify": SkillSpec(
        id="verify",
        name="Verification",
        purpose="Check whether important claims are actually supported, current, and non-contradictory.",
        default_automation="augment",
        human_role="Decide what level of evidence is sufficient for the real-world consequence.",
        requires_verification=True,
        steps=("extract claims", "classify verification need", "match evidence", "seek contradiction", "calibrate confidence"),
        stop_condition="Material claims are verified, corrected, or explicitly marked unverified.",
        eval_dimensions=("groundedness", "accuracy", "recency", "calibration"),
        maturity="executable", executor="verification.verify_claim",
    ),
    "decision": SkillSpec(
        id="decision",
        name="Decision Support",
        purpose="Structure options and trade-offs without taking human ownership of value judgments.",
        default_automation="augment",
        human_role="Make the value judgment and final decision.",
        requires_verification=True,
        steps=("define objective", "identify options", "surface assumptions", "compare trade-offs", "state reversible next step"),
        stop_condition="The user can explain why the preferred option fits their values and constraints.",
        eval_dimensions=("assumption_quality", "tradeoff_coverage", "decision_clarity", "safety"),
        maturity="assisted", executor="executive+reasoning",
    ),
    "reflection": SkillSpec(
        id="reflection",
        name="Reflection & Learning",
        purpose="Turn outcomes into reusable learning rather than merely adding another memory.",
        default_automation="augment",
        human_role="Interpret why the result mattered and what should change next time.",
        requires_verification=False,
        steps=("record expectation", "record outcome", "identify mismatch", "generate lessons", "propose next-rule update"),
        stop_condition="A concrete lesson and a future check are recorded.",
        eval_dimensions=("outcome_linkage", "lesson_specificity", "transferability"),
        maturity="executable", executor="learning.propose_reflection",
    ),
    "brief": SkillSpec(
        id="brief",
        name="Brief",
        purpose="Surface only what deserves attention now and suppress low-value noise.",
        default_automation="auto",
        human_role="Override salience when personal priorities differ from system estimates.",
        requires_verification=False,
        steps=("collect candidates", "score salience", "deduplicate", "surface few items"),
        stop_condition="The brief contains only items that may change today's action or understanding.",
        eval_dimensions=("salience", "noise_rate", "actionability"),
        maturity="executable", executor="attention.attention_items+brief",
    ),
}


def get_skill(skill_id: str) -> SkillSpec:
    return SKILLS[skill_id]


def list_skills(ids: Iterable[str] | None = None) -> list[dict]:
    if ids is None:
        return [s.to_dict() for s in SKILLS.values()]
    return [SKILLS[sid].to_dict() for sid in ids if sid in SKILLS]


def skill_instructions(skill_ids: Iterable[str]) -> str:
    lines: list[str] = []
    for sid in skill_ids:
        skill = SKILLS.get(sid)
        if not skill:
            continue
        lines.append(
            f"[{skill.name}] Purpose: {skill.purpose} Steps: {' -> '.join(skill.steps)} "
            f"Human role: {skill.human_role} Stop when: {skill.stop_condition}"
        )
    return "\n".join(lines)
