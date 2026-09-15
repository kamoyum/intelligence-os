from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class EvalProfile:
    level: str  # light | standard | deep | high_stakes
    label: str
    verification_required: bool
    require_counterevidence: bool
    require_primary_sources: bool
    require_current_sources: bool
    external_judge: str  # skip | optional | preferred
    human_review: str  # none | review | decide
    rationale: tuple[str, ...]

    def to_dict(self) -> dict:
        out = asdict(self)
        out["rationale"] = list(self.rationale)
        return out


_FINANCIAL_RULE_PATTERNS = (
    r"NISA", r"iDeCo", r"投資", r"税", r"控除", r"保険", r"ローン", r"年金",
    r"tax", r"investment", r"pension", r"insurance", r"loan",
)

_HEALTH_HIGH_STAKES_PATTERNS = (
    r"抜歯", r"術後", r"手術", r"薬", r"服薬", r"症状", r"救急", r"診断", r"治療", r"患者",
    r"post[- ]?op", r"surgery", r"medication", r"diagnos", r"treatment", r"patient",
)

_LEGAL_HIGH_STAKES_PATTERNS = (
    r"法律", r"契約", r"訴訟", r"違法", r"法的", r"legal", r"contract", r"lawsuit",
)


def _match_any(text: str, patterns: Iterable[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def build_eval_profile(
    query: str,
    *,
    risk: str,
    cognitive_value: str,
    freshness: str,
    evidence_requirement: str,
    skills: Iterable[str],
    query_safety_level: str,
) -> EvalProfile:
    """Scale evaluation effort without weakening the always-on Base Policy.

    Adaptive Evals changes *how much additional checking* is required. It never disables
    privacy, anti-fabrication, uncertainty, or human-authority safeguards.
    """
    q = query.strip()
    skill_set = set(skills)
    rationale: list[str] = []

    domain_high_stakes = _match_any(q, _HEALTH_HIGH_STAKES_PATTERNS) or _match_any(q, _LEGAL_HIGH_STAKES_PATTERNS)
    finance_deep = _match_any(q, _FINANCIAL_RULE_PATTERNS)

    if query_safety_level == "secret":
        level = "high_stakes"
        rationale.append("The query contains a secret/credential boundary; external transmission and evaluation require the strictest handling.")
    elif risk in {"high", "critical"} or domain_high_stakes:
        level = "high_stakes"
        rationale.append("The task is high-stakes or health/legal consequential; stronger evidence and explicit human judgment are required.")
    elif evidence_requirement == "current_primary" or freshness == "current":
        level = "deep"
        rationale.append("The answer depends on current information; primary/current evidence and contradiction checks are required.")
    elif finance_deep:
        level = "deep"
        rationale.append("Financial/tax/pension rules are context- and time-sensitive; deeper verification is required.")
    elif "research" in skill_set and "verify" in skill_set:
        level = "deep"
        rationale.append("The task explicitly requires research plus verification.")
    elif cognitive_value == "high" or "decision" in skill_set or "reflection" in skill_set:
        level = "standard"
        rationale.append("The task benefits from structured evaluation but does not automatically require full current-source research.")
    else:
        level = "light"
        rationale.append("The task is low-risk, stable, and mostly mechanical; lightweight checks are sufficient.")

    if level == "light":
        return EvalProfile(
            level=level,
            label="Level 1 — Light",
            verification_required=False,
            require_counterevidence=False,
            require_primary_sources=False,
            require_current_sources=False,
            external_judge="skip",
            human_review="none",
            rationale=tuple(rationale),
        )
    if level == "standard":
        return EvalProfile(
            level=level,
            label="Level 2 — Standard",
            verification_required="verify" in skill_set,
            require_counterevidence=False,
            require_primary_sources=False,
            require_current_sources=False,
            external_judge="optional",
            human_review="review",
            rationale=tuple(rationale),
        )
    if level == "deep":
        return EvalProfile(
            level=level,
            label="Level 3 — Deep",
            verification_required=True,
            require_counterevidence=True,
            require_primary_sources=True,
            require_current_sources=freshness == "current" or evidence_requirement == "current_primary" or finance_deep,
            external_judge="preferred",
            human_review="review",
            rationale=tuple(rationale),
        )
    return EvalProfile(
        level="high_stakes",
        label="Level 4 — High-Stakes",
        verification_required=True,
        require_counterevidence=True,
        require_primary_sources=True,
        require_current_sources=True,
        external_judge="preferred",
        human_review="decide",
        rationale=tuple(rationale),
    )
