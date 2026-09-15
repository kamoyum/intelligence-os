from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .query_safety import classify_query_safety
from .quality_harness import build_eval_profile
from .skills import list_skills


@dataclass(frozen=True)
class ExecutivePlan:
    goal: str
    autonomy: str  # auto | augment | human_only
    risk: str  # low | medium | high | critical
    cognitive_value: str  # low | high
    cognitive_mode: str  # offload | collaborate | human_lead
    freshness: str  # stable | current
    evidence_requirement: str  # none | local | current_primary
    query_safety: dict
    skills: tuple[str, ...]
    human_role: str
    human_checkpoint: str  # none | review | decide | redact
    thinking_prompt: str
    human_first_prompt: str
    stop_condition: str
    rationale: tuple[str, ...]
    eval_profile: dict

    def to_dict(self) -> dict:
        d = asdict(self)
        d["skills"] = list(self.skills)
        d["rationale"] = list(self.rationale)
        d["skill_specs"] = list_skills(self.skills)
        return d


LOW_VALUE_PATTERNS = (
    r"要約", r"まとめ", r"整理", r"抽出", r"転記", r"整形", r"分類", r"一覧", r"フォーマット",
    r"summari[sz]e", r"extract", r"format", r"organize", r"classify",
)
HIGH_VALUE_PATTERNS = (
    r"なぜ", r"仮説", r"判断", r"意思決定", r"比較", r"戦略", r"設計", r"研究", r"臨床推論", r"考察",
    r"創造", r"アイデア", r"反証", r"どう思う", r"evaluate", r"decide", r"strategy", r"hypothesis", r"design",
)
CURRENT_PATTERNS = (
    r"最新", r"現在", r"今日", r"直近", r"いま", r"今週", r"current", r"latest", r"today", r"recent",
)
HIGH_RISK_PATTERNS = (
    r"患者", r"診断", r"治療", r"投薬", r"服薬", r"抜歯", r"術後", r"手術", r"救急", r"医療判断",
    r"契約", r"法律判断", r"法的判断", r"投資判断", r"購入", r"送信", r"公開",
    r"削除", r"権限", r"個人情報", r"patient", r"diagnos", r"treatment", r"medication", r"surgery",
    r"contract", r"legal decision", r"purchase", r"send", r"delete",
)
CRITICAL_PATTERNS = (
    r"自動で.*送信", r"勝手に.*削除", r"権限.*増", r"不可逆", r"self-authoriz", r"permission escalation",
)
RESEARCH_PATTERNS = (
    r"調べ", r"検索", r"文献", r"エビデンス", r"根拠", r"ファクトチェック", r"research", r"evidence", r"source", r"verify",
)
DECISION_PATTERNS = (r"どっち", r"おすすめ", r"選ぶ", r"判断", r"決め", r"decision", r"recommend")
REFLECTION_PATTERNS = (r"振り返", r"結果", r"予測", r"学び", r"改善", r"reflection", r"outcome", r"learn")


def _match_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def plan(query: str) -> ExecutivePlan:
    q = query.strip()
    qsafe = classify_query_safety(q)
    high_value = _match_any(q, HIGH_VALUE_PATTERNS)
    low_value = _match_any(q, LOW_VALUE_PATTERNS) and not high_value
    current = _match_any(q, CURRENT_PATTERNS)
    research = current or _match_any(q, RESEARCH_PATTERNS)
    decision = _match_any(q, DECISION_PATTERNS)
    reflection = _match_any(q, REFLECTION_PATTERNS)

    if _match_any(q, CRITICAL_PATTERNS):
        risk = "critical"
    elif _match_any(q, HIGH_RISK_PATTERNS) or qsafe.level == "sensitive":
        risk = "high"
    elif decision or research:
        risk = "medium"
    else:
        risk = "low"

    cognitive_value = "low" if low_value else "high" if high_value or decision or reflection else "low"
    freshness = "current" if current else "stable"

    if risk in {"high", "critical"}:
        evidence_requirement = "current_primary"
    elif research and current:
        evidence_requirement = "current_primary"
    elif research or decision:
        evidence_requirement = "local"
    else:
        evidence_requirement = "none"

    skills: list[str] = ["memory_context"]
    rationale: list[str] = []

    if low_value:
        skills.append("organize")
        rationale.append("The task is primarily repetitive/structuring work, so automation can reduce low-value cognitive load.")
    if research:
        skills.extend(["research", "verify"])
        rationale.append("The task depends on evidence or current information; reasoning alone is not sufficient.")
    if decision:
        skills.extend(["decision", "verify"])
        rationale.append("The task includes a choice; AI should structure trade-offs while the human owns the value judgment.")
    if reflection:
        skills.append("reflection")
        rationale.append("The task references outcomes or improvement, so learning should be captured explicitly.")
    if risk in {"high", "critical"}:
        skills.extend(["research", "verify"])
        rationale.append("High-stakes tasks require stronger evidence handling; external research remains permission-gated by privacy/risk policy.")
    if qsafe.level == "secret":
        rationale.append("The query appears to contain a credential/secret; external transmission must be blocked until redacted.")
    elif qsafe.level == "sensitive":
        rationale.append("The query may contain personal/sensitive context; external research requires an explicit checkpoint.")
    if not rationale:
        rationale.append("Use relevant memory and keep the workflow minimal unless the task reveals additional risk or evidence needs.")

    skills = list(dict.fromkeys(skills))

    if qsafe.level == "secret":
        autonomy = "human_only"
        human_checkpoint = "redact"
    elif risk == "critical":
        autonomy = "human_only"
        human_checkpoint = "decide"
    elif risk == "high":
        autonomy = "augment"
        human_checkpoint = "decide" if decision else "review"
    elif cognitive_value == "high":
        autonomy = "augment"
        human_checkpoint = "decide" if decision else "review"
    else:
        autonomy = "auto"
        human_checkpoint = "none"

    if autonomy == "auto":
        cognitive_mode = "offload"
        human_role = "Set the goal and review only if the output changes meaning or triggers a real-world action."
        thinking_prompt = "You do not need to spend attention on the mechanical work; review the result for meaning and exceptions."
        human_first_prompt = ""
    elif autonomy == "augment":
        cognitive_mode = "collaborate"
        human_role = "Form or confirm the hypothesis/value judgment; use AI for evidence, structure, alternatives, and critique."
        thinking_prompt = "Before accepting the answer, state what you think matters most and what evidence would change your mind."
        human_first_prompt = "Before seeing the synthesis, write your current hypothesis, decision criterion, or what evidence would change your mind."
    else:
        cognitive_mode = "human_lead"
        human_role = "Own the decision and action. AI may organize evidence and risks but must not execute or decide autonomously."
        thinking_prompt = "Make the decision yourself after reviewing assumptions, alternatives, and consequences."
        human_first_prompt = "State your intended decision and the assumptions behind it before using AI as a critic or evidence assistant."

    if qsafe.level == "secret":
        stop_condition = "Stop before any external model/search call until secrets are removed or the query is rewritten locally."
    elif autonomy == "auto":
        stop_condition = "Stop when the requested low-risk transformation is complete and meaning is preserved."
    else:
        stop_condition = "Stop when material uncertainty, assumptions, evidence status, and trade-offs are explicit enough for the human to decide."

    eval_profile = build_eval_profile(
        q, risk=risk, cognitive_value=cognitive_value, freshness=freshness,
        evidence_requirement=evidence_requirement, skills=skills, query_safety_level=qsafe.level,
    ).to_dict()

    return ExecutivePlan(
        goal=q[:300], autonomy=autonomy, risk=risk, cognitive_value=cognitive_value, cognitive_mode=cognitive_mode, freshness=freshness,
        evidence_requirement=evidence_requirement, query_safety=qsafe.to_dict(),
        skills=tuple(skills), human_role=human_role, human_checkpoint=human_checkpoint,
        thinking_prompt=thinking_prompt, human_first_prompt=human_first_prompt, stop_condition=stop_condition, rationale=tuple(rationale),
        eval_profile=eval_profile,
    )
