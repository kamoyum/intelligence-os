from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .retrieval import tokenize
from .storage import connect, now_iso


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def create_goal(
    title: str,
    *,
    description: str = "",
    priority: float = 0.7,
    due_at: str | None = None,
    tags: list[str] | None = None,
    db_path: Path | None = None,
) -> int:
    priority = max(0.0, min(1.0, float(priority)))
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO goals(created_at,title,description,priority,due_at,tags,status) VALUES(?,?,?,?,?,?,?)",
            (now_iso(), title.strip(), description.strip(), priority, due_at, __import__("json").dumps(tags or [], ensure_ascii=False), "active"),
        )
        return int(cur.lastrowid)


def list_goals(*, include_inactive: bool = False, db_path: Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        if include_inactive:
            rows = conn.execute("SELECT * FROM goals ORDER BY status='active' DESC,priority DESC,id DESC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM goals WHERE status='active' ORDER BY priority DESC,id DESC").fetchall()
    return [dict(r) for r in rows]


def set_goal_status(goal_id: int, status: str, *, db_path: Path | None = None) -> None:
    if status not in {"active", "paused", "done"}:
        raise ValueError("status must be active/paused/done")
    with connect(db_path) as conn:
        cur = conn.execute("UPDATE goals SET status=? WHERE id=?", (status, goal_id))
        if cur.rowcount == 0:
            raise KeyError(goal_id)


def _goal_relevance(memory: dict[str, Any], goals: list[dict[str, Any]]) -> tuple[float, list[str]]:
    if not goals:
        return 0.0, []
    mt = set(tokenize(f"{memory.get('title','')} {memory.get('summary','')}"))
    best = 0.0
    reasons: list[str] = []
    for goal in goals:
        gt = set(tokenize(f"{goal.get('title','')} {goal.get('description','')} {goal.get('tags','')}"))
        if not gt:
            continue
        overlap = len(mt & gt) / max(1, len(gt))
        weighted = min(1.0, overlap * (0.55 + 0.45 * float(goal.get("priority") or 0.0)))
        if weighted > best:
            best = weighted
            if overlap >= 0.12:
                reasons = [f"goal:{goal.get('title','')}"]
    return best, reasons


def _recency(created_at: str | None) -> float:
    dt = _parse_dt(created_at)
    if not dt:
        return 0.5
    age_days = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0)
    return max(0.15, 1.0 / (1.0 + age_days / 21.0))


def attention_items(limit: int = 8, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    goals = list_goals(db_path=db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id,created_at,title,url,importance,summary,tags FROM memories WHERE status='active' ORDER BY id DESC LIMIT 250"
        ).fetchall()
    ranked: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        relevance, reasons = _goal_relevance(item, goals)
        recency = _recency(item.get("created_at"))
        importance = max(0.0, min(1.0, float(item.get("importance") or 0.0)))
        # Goal relevance is the largest term because attention should follow human intent, not only
        # what the system happened to score as important at capture time.
        score = 0.48 * relevance + 0.32 * importance + 0.20 * recency
        why = list(reasons)
        if importance >= 0.75:
            why.append("high_importance")
        if recency >= 0.75:
            why.append("recent")
        item.update({
            "attention_score": round(score, 3),
            "goal_relevance": round(relevance, 3),
            "recency": round(recency, 3),
            "why": why or ["baseline"],
        })
        ranked.append(item)
    ranked.sort(key=lambda x: (x["attention_score"], x["id"]), reverse=True)
    return ranked[: max(1, min(limit, 30))]


def due_expectations(*, include_upcoming_hours: int = 24, db_path: Path | None = None) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id,created_at,prediction_text,expected_result,confidence,due_at,status FROM expectations WHERE status='open' AND due_at IS NOT NULL ORDER BY due_at ASC"
        ).fetchall()
    out: list[dict[str, Any]] = []
    horizon_seconds = max(0, include_upcoming_hours) * 3600
    for row in rows:
        item = dict(row)
        due = _parse_dt(item.get("due_at"))
        if not due:
            continue
        seconds = (due - now).total_seconds()
        if seconds <= horizon_seconds:
            item["due_state"] = "overdue" if seconds < 0 else "due_soon"
            item["seconds_to_due"] = int(seconds)
            out.append(item)
    return out


def _goal_urgency(due_at: str | None) -> float:
    due = _parse_dt(due_at)
    if not due:
        return 0.35
    seconds = (due - datetime.now(timezone.utc)).total_seconds()
    if seconds <= 0:
        return 1.0
    days = seconds / 86400.0
    if days <= 1:
        return 0.95
    if days <= 3:
        return 0.82
    if days <= 7:
        return 0.68
    if days <= 30:
        return 0.48
    return 0.3


def attention_queue(limit: int = 12, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    """Unified attention queue across memory, goals, knowledge conflicts, approvals and due outcomes.

    The queue is a prioritization aid, not an instruction to act. Human goals and explicit deadlines
    outrank generic memory importance. Items that can change real-world state remain proposals only.
    """
    items: list[dict[str, Any]] = []

    for m in attention_items(limit=12, db_path=db_path):
        items.append({
            "type": "memory",
            "id": m["id"],
            "title": m["title"],
            "score": round(float(m["attention_score"]) * 0.78, 3),
            "why": m.get("why", []),
            "url": m.get("url"),
        })

    for g in list_goals(db_path=db_path):
        priority = max(0.0, min(1.0, float(g.get("priority") or 0.0)))
        urgency = _goal_urgency(g.get("due_at"))
        score = 0.58 * priority + 0.42 * urgency
        items.append({
            "type": "goal",
            "id": g["id"],
            "title": g["title"],
            "score": round(score, 3),
            "why": ["active_goal"] + (["deadline"] if g.get("due_at") else []),
            "due_at": g.get("due_at"),
        })

    for d in due_expectations(include_upcoming_hours=24 * 7, db_path=db_path):
        score = 0.98 if d.get("due_state") == "overdue" else 0.86
        items.append({
            "type": "outcome_due",
            "id": d["id"],
            "title": d["prediction_text"],
            "score": score,
            "why": [d.get("due_state", "due")],
            "due_at": d.get("due_at"),
        })

    with connect(db_path) as conn:
        claims = conn.execute(
            "SELECT id,claim_text,status,confidence FROM claims WHERE status IN ('contested','contradicted') ORDER BY confidence DESC,id DESC LIMIT 20"
        ).fetchall()
        approvals = conn.execute(
            "SELECT id,description,risk FROM approvals WHERE status='pending' ORDER BY id DESC LIMIT 20"
        ).fetchall()
        failed_research = conn.execute(
            "SELECT id,query,error FROM research_runs WHERE status='failed' ORDER BY id DESC LIMIT 10"
        ).fetchall()

    for c in claims:
        base = 0.92 if c["status"] == "contested" else 0.88
        score = min(1.0, base + 0.05 * float(c["confidence"] or 0.0))
        items.append({
            "type": "knowledge_conflict",
            "id": c["id"],
            "title": c["claim_text"],
            "score": round(score, 3),
            "why": [c["status"], "human_review"],
        })

    risk_score = {"critical": 1.0, "high": 0.94, "medium": 0.78, "low": 0.6}
    for a in approvals:
        items.append({
            "type": "approval",
            "id": a["id"],
            "title": a["description"],
            "score": risk_score.get(str(a["risk"]), 0.7),
            "why": ["pending_approval", str(a["risk"])],
        })

    for r in failed_research:
        items.append({
            "type": "research_failure",
            "id": r["id"],
            "title": r["query"],
            "score": 0.74,
            "why": ["research_failed", "do_not_guess"],
            "error": r["error"],
        })

    items.sort(key=lambda x: (float(x.get("score") or 0.0), str(x.get("type")), int(x.get("id") or 0)), reverse=True)
    return items[: max(1, min(limit, 50))]
