from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .storage import connect, now_iso



VALID_FEEDBACK_SIGNALS = {
    "helped_me_think",
    "saved_repetitive_work",
    "caught_an_error",
    "too_much_noise",
    "made_me_think_less",
    "wrong_or_unsafe",
}


def record_feedback(signal: str, *, task_id: int | None = None, note: str = "", db_path: Path | None = None) -> int:
    if signal not in VALID_FEEDBACK_SIGNALS:
        raise ValueError(f"Unsupported feedback signal: {signal}")
    with connect(db_path) as conn:
        if task_id is not None and not conn.execute("SELECT 1 FROM tasks WHERE id=?", (task_id,)).fetchone():
            raise KeyError(task_id)
        cur = conn.execute(
            "INSERT INTO feedback_events(created_at,task_id,signal,note) VALUES(?,?,?,?)",
            (now_iso(), task_id, signal, note.strip()[:2000]),
        )
        return int(cur.lastrowid)


def feedback_summary(*, db_path: Path | None = None) -> dict[str, int]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT signal,COUNT(*) n FROM feedback_events GROUP BY signal").fetchall()
    return {r["signal"]: int(r["n"]) for r in rows}

def record_skill_run(
    skill_id: str,
    *,
    status: str,
    task_id: int | None = None,
    mode: str = "observed",
    executor: str | None = None,
    duration_ms: int | None = None,
    metrics: dict[str, Any] | None = None,
    error: str = "",
    db_path: Path | None = None,
) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO skill_runs(created_at,task_id,skill_id,status,mode,executor,duration_ms,metrics,error) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                now_iso(), task_id, skill_id, status, mode, executor, duration_ms,
                json.dumps(metrics or {}, ensure_ascii=False), error[:2000],
            ),
        )
        return int(cur.lastrowid)


def list_skill_runs(limit: int = 100, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM skill_runs ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        d = dict(row)
        try:
            d["metrics"] = json.loads(d.get("metrics") or "{}")
        except Exception:
            d["metrics"] = {}
        out.append(d)
    return out


def _safe_ratio(num: int | float, den: int | float) -> float | None:
    if not den:
        return None
    return round(float(num) / float(den), 3)


def system_evals(*, db_path: Path | None = None) -> dict[str, Any]:
    """Operational Evals for the OS itself.

    These are observability signals, not proof that Intelligence OS improves human cognition.
    They are designed to reveal regressions and whether core loops are actually being exercised.
    """
    with connect(db_path) as conn:
        task_row = conn.execute(
            "SELECT COUNT(*) total, SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) done FROM tasks"
        ).fetchone()
        ask_tasks = int(conn.execute("SELECT COUNT(*) n FROM tasks WHERE kind='ask'").fetchone()["n"])
        eval_row = conn.execute(
            "SELECT AVG(accuracy) accuracy,AVG(groundedness) groundedness,AVG(relevance) relevance,AVG(actionability) actionability,AVG(safety) safety FROM evals"
        ).fetchone()
        research = {r["status"]: int(r["n"]) for r in conn.execute("SELECT status,COUNT(*) n FROM research_runs GROUP BY status")}
        claims = {r["status"]: int(r["n"]) for r in conn.execute("SELECT status,COUNT(*) n FROM claims GROUP BY status")}
        lessons = {r["status"]: int(r["n"]) for r in conn.execute("SELECT status,COUNT(*) n FROM lessons GROUP BY status")}
        approvals = {r["status"]: int(r["n"]) for r in conn.execute("SELECT status,COUNT(*) n FROM approvals GROUP BY status")}
        memory_count = int(conn.execute("SELECT COUNT(*) n FROM memories WHERE status='active'").fetchone()["n"])
        hard_local = int(conn.execute(
            "SELECT COUNT(*) n FROM memories WHERE status='active' AND (source_type IN ('gmail','google_drive','google_calendar') OR sensitivity IN ('sensitive','highly_sensitive'))"
        ).fetchone()["n"])
        skill_rows = conn.execute("SELECT skill_id,status,COUNT(*) n FROM skill_runs GROUP BY skill_id,status").fetchall()
        metric_rows = conn.execute("SELECT skill_id,metrics FROM skill_runs WHERE status='done'").fetchall()
        feedback_rows = conn.execute("SELECT signal,COUNT(*) n FROM feedback_events GROUP BY signal").fetchall()
        action_rows = conn.execute("SELECT status,COUNT(*) n FROM action_runs GROUP BY status").fetchall()

    feedback = {r["signal"]: int(r["n"]) for r in feedback_rows}
    actions = {r["status"]: int(r["n"]) for r in action_rows}
    skill_summary: dict[str, dict[str, int]] = {}
    for r in skill_rows:
        skill_summary.setdefault(r["skill_id"], {})[r["status"]] = int(r["n"])

    memory_context_runs = 0
    memory_reuse_runs = 0
    for r in metric_rows:
        if r["skill_id"] != "memory_context":
            continue
        memory_context_runs += 1
        try:
            m = json.loads(r["metrics"] or "{}")
        except Exception:
            m = {}
        if int(m.get("retrieved", 0) or 0) > 0:
            memory_reuse_runs += 1

    research_done = int(research.get("done", 0))
    research_failed = int(research.get("failed", 0))
    accepted = int(lessons.get("accepted", 0))
    rejected = int(lessons.get("rejected", 0))
    verified = int(claims.get("verified", 0))
    contested = int(claims.get("contested", 0)) + int(claims.get("contradicted", 0))

    avg_evals = {
        k: (round(float(eval_row[k]), 3) if eval_row[k] is not None else None)
        for k in ("accuracy", "groundedness", "relevance", "actionability", "safety")
    }
    signals = {
        "task_completion_rate": _safe_ratio(int(task_row["done"] or 0), int(task_row["total"] or 0)),
        "memory_reuse_rate_per_memory_skill_run": _safe_ratio(memory_reuse_runs, memory_context_runs),
        "research_success_rate": _safe_ratio(research_done, research_done + research_failed),
        "lesson_acceptance_rate": _safe_ratio(accepted, accepted + rejected),
        "verified_claim_share": _safe_ratio(verified, sum(claims.values())),
        "unresolved_contradiction_count": contested,
        "pending_approval_count": int(approvals.get("pending", 0)),
        "human_thinking_helped_count": int(feedback.get("helped_me_think", 0)),
        "repetitive_work_saved_count": int(feedback.get("saved_repetitive_work", 0)),
        "thinking_reduction_warning_count": int(feedback.get("made_me_think_less", 0)),
        "wrong_or_unsafe_feedback_count": int(feedback.get("wrong_or_unsafe", 0)),
        "auto_local_actions_done": int(actions.get("done", 0)),
        "actions_awaiting_approval": int(actions.get("awaiting_approval", 0)),
        "actions_undone": int(actions.get("undone", 0)),
    }
    readiness_flags: list[str] = []
    if ask_tasks == 0:
        readiness_flags.append("no_real_usage_yet")
    if research_failed > 0 and research_done == 0:
        readiness_flags.append("research_provider_not_proven")
    if contested > 0:
        readiness_flags.append("knowledge_conflicts_need_review")
    if memory_context_runs and memory_reuse_runs == 0:
        readiness_flags.append("memory_not_reused_yet")
    if int(feedback.get("made_me_think_less", 0)) > 0:
        readiness_flags.append("human_cognitive_agency_warning")
    if int(feedback.get("wrong_or_unsafe", 0)) > 0:
        readiness_flags.append("wrong_or_unsafe_feedback_needs_review")

    return {
        "generated_at": now_iso(),
        "scope": "local_operational_evals",
        "limitations": [
            "These signals measure system behavior, not whether human cognition, judgment, or productivity improved.",
            "Rates can be misleading with small sample sizes; inspect raw counts before interpreting trends.",
        ],
        "counts": {
            "tasks_total": int(task_row["total"] or 0),
            "ask_tasks": ask_tasks,
            "active_memories": memory_count,
            "hard_local_memories": hard_local,
            "research": research,
            "claims": claims,
            "lessons": lessons,
            "approvals": approvals,
            "feedback": feedback,
            "actions": actions,
        },
        "average_task_evals": avg_evals,
        "skills": skill_summary,
        "signals": signals,
        "readiness_flags": readiness_flags,
    }
