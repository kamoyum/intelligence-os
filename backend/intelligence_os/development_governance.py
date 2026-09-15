from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class DevelopmentPolicy:
    name: str = "safety_limited_velocity"
    description: str = (
        "Advance capabilities only as fast as evidence, safeguards, rollback, and human governance can keep up."
    )
    max_new_authority_boundaries_per_release: int = 1
    min_eval_coverage_for_expansion: float = 0.90
    min_redteam_coverage_for_expansion: float = 0.90
    min_observation_days_external_write: int = 14
    require_rollback_for_autonomous_action: bool = True
    require_zero_open_critical_incidents: bool = True
    freeze_on_privacy_regression: bool = True
    freeze_on_safety_benchmark_regression: bool = True
    external_authority_expansion_requires_human_review: bool = True


POLICY = DevelopmentPolicy()


def policy_snapshot() -> dict[str, Any]:
    return asdict(POLICY)


def evaluate_capability(
    *,
    capability: str,
    risk: str,
    external_side_effect: bool,
    permission_expansion: bool,
    reversible: bool,
    eval_coverage: float,
    redteam_coverage: float,
    rollback_tested: bool,
    open_critical_incidents: int = 0,
    privacy_regression: bool = False,
    safety_benchmark_regression: bool = False,
    observation_days: int = 0,
    real_world_evidence: bool = False,
    new_authority_boundaries: int = 0,
) -> dict[str, Any]:
    """Conservative release/capability gate for Intelligence OS.

    The gate is intentionally asymmetric: evidence can permit a bounded experiment,
    but missing evidence never implies permission to expand authority.
    """
    risk = (risk or "medium").lower().strip()
    blockers: list[str] = []
    cautions: list[str] = []

    if open_critical_incidents > 0 and POLICY.require_zero_open_critical_incidents:
        blockers.append("open_critical_incident")
    if privacy_regression and POLICY.freeze_on_privacy_regression:
        blockers.append("privacy_regression")
    if safety_benchmark_regression and POLICY.freeze_on_safety_benchmark_regression:
        blockers.append("safety_benchmark_regression")
    if new_authority_boundaries > POLICY.max_new_authority_boundaries_per_release:
        blockers.append("too_many_authority_boundaries_in_one_release")

    if permission_expansion:
        blockers.append("permission_expansion_requires_separate_human_governance")

    if risk in {"high", "critical"}:
        cautions.append("high_risk_capability")

    if eval_coverage < POLICY.min_eval_coverage_for_expansion:
        cautions.append("insufficient_eval_coverage")
    if redteam_coverage < POLICY.min_redteam_coverage_for_expansion:
        cautions.append("insufficient_redteam_coverage")

    if external_side_effect:
        if observation_days < POLICY.min_observation_days_external_write:
            cautions.append("insufficient_observation_window")
        if not real_world_evidence:
            cautions.append("no_real_world_evidence")

    if not reversible and POLICY.require_rollback_for_autonomous_action:
        blockers.append("irreversible_autonomy_not_allowed")
    elif not rollback_tested and not external_side_effect:
        cautions.append("rollback_not_tested")

    if blockers:
        decision = "HOLD"
    else:
        evidence_ready = (
            eval_coverage >= POLICY.min_eval_coverage_for_expansion
            and redteam_coverage >= POLICY.min_redteam_coverage_for_expansion
        )
        external_ready = (
            not external_side_effect
            or (
                observation_days >= POLICY.min_observation_days_external_write
                and real_world_evidence
            )
        )
        if risk in {"high", "critical"} or not evidence_ready or not external_ready:
            decision = "CONTAINED_ALPHA"
        else:
            decision = "ELIGIBLE_FOR_BOUNDED_EXPANSION"

    authority = "human_only" if external_side_effect or permission_expansion or risk in {"high", "critical"} else "bounded_auto"

    return {
        "capability": capability,
        "policy": POLICY.name,
        "decision": decision,
        "authority": authority,
        "blockers": blockers,
        "cautions": cautions,
        "principle": "Safety evidence must lead capability/authority expansion; speed is not itself a success metric.",
    }


def capability_registry() -> list[dict[str, Any]]:
    """Human-readable capability/authority map.

    The registry is intentionally conservative: a capability can exist while its
    authority remains proposal-only or human-only.
    """
    return [
        {"capability": "memory_context", "state": "active", "authority": "local", "notes": "Local-first Memory/Context."},
        {"capability": "web_research", "state": "contained_alpha", "authority": "bounded_external_read", "notes": "Query Safety + daily cap + evidence ingestion."},
        {"capability": "verification", "state": "active_alpha", "authority": "advisory", "notes": "Evidence-policy status; not absolute truth."},
        {"capability": "outcome_learning", "state": "active_alpha", "authority": "human_supervised", "notes": "Lessons require human acceptance."},
        {"capability": "create_local_note", "state": "bounded_auto", "authority": "local_reversible", "notes": "Auto-execute + Undo."},
        {"capability": "gmail_draft", "state": "proposal_only", "authority": "human_approval", "notes": "No live external executor in this release."},
        {"capability": "calendar_event", "state": "proposal_only", "authority": "human_approval", "notes": "No live external executor in this release."},
        {"capability": "drive_artifact", "state": "proposal_only", "authority": "human_approval", "notes": "No live external executor in this release."},
        {"capability": "email_send", "state": "disabled_external_execution", "authority": "human_only", "notes": "Consequential external action."},
        {"capability": "publish_delete_permission", "state": "disabled_external_execution", "authority": "human_only", "notes": "No autonomous irreversible/permission-changing action."},
        {"capability": "mobile_client", "state": "planned_staged", "authority": "thin_client", "notes": "Capture/read/approval first; action authority later only after gate."},
    ]
