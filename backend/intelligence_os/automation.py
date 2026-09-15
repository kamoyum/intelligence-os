from __future__ import annotations

from typing import Any


def action_policy(*, risk: str, reversible: bool = True, external_side_effect: bool = False) -> dict[str, Any]:
    """Translate consequence/risk into an execution policy.

    This policy intentionally separates cognitive automation from real-world authority.
    """
    if risk == "critical":
        return {"mode": "human_only", "approval_required": True, "auto_execute": False, "reason": "Critical or permission-expanding action."}
    if risk == "high" or external_side_effect:
        return {"mode": "approve", "approval_required": True, "auto_execute": False, "reason": "External or high-impact action requires explicit human approval."}
    if risk == "medium" or not reversible:
        return {"mode": "notify", "approval_required": not reversible, "auto_execute": reversible, "reason": "Moderate consequence; keep the user informed and preserve reversibility."}
    return {"mode": "auto", "approval_required": False, "auto_execute": True, "reason": "Low-risk reversible operation can be automated."}
