from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .automation import action_policy
from .retrieval import index_memory
from .storage import clean_summary, connect, insert_memory, now_iso


@dataclass(frozen=True)
class ActionSpec:
    action_type: str
    risk: str
    reversible: bool
    external_side_effect: bool
    executor: str | None
    description: str


ACTION_SPECS: dict[str, ActionSpec] = {
    "create_local_note": ActionSpec(
        "create_local_note", "low", True, False, "local_note",
        "Create a private local Memory note inside Intelligence OS.",
    ),
    "gmail_draft": ActionSpec(
        "gmail_draft", "medium", True, True, None,
        "Propose creating a Gmail draft. v0.7.2-alpha does not execute this external write.",
    ),
    "calendar_event": ActionSpec(
        "calendar_event", "medium", True, True, None,
        "Propose creating or changing a calendar event. External write remains disabled.",
    ),
    "drive_artifact": ActionSpec(
        "drive_artifact", "medium", True, True, None,
        "Propose creating a Drive artifact. External write remains disabled.",
    ),
    "email_send": ActionSpec(
        "email_send", "high", False, True, None,
        "Sending email is consequential and is never silently executed.",
    ),
    "publish_external": ActionSpec(
        "publish_external", "high", False, True, None,
        "External publication requires explicit human control.",
    ),
    "delete_external": ActionSpec(
        "delete_external", "high", False, True, None,
        "External deletion is not executed by this alpha.",
    ),
    "permission_change": ActionSpec(
        "permission_change", "critical", False, True, None,
        "Permission expansion is human-only.",
    ),
}


def list_action_specs() -> list[dict[str, Any]]:
    return [
        {
            "action_type": s.action_type,
            "risk": s.risk,
            "reversible": s.reversible,
            "external_side_effect": s.external_side_effect,
            "executor": s.executor,
            "description": s.description,
        }
        for s in ACTION_SPECS.values()
    ]


def _create_approval(action_type: str, description: str, risk: str, payload: dict[str, Any], *, db_path: Path | None = None) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO approvals(created_at,action_type,description,risk,status,payload) VALUES(?,?,?,?,?,?)",
            (now_iso(), action_type, description, risk, "pending", json.dumps(payload, ensure_ascii=False)),
        )
        return int(cur.lastrowid)


def _execute_local_note(payload: dict[str, Any], *, db_path: Path | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    title = str(payload.get("title") or "Local note").strip()[:500]
    content = str(payload.get("content") or "").strip()
    if not content:
        raise ValueError("create_local_note requires payload.content")
    tags = payload.get("tags") if isinstance(payload.get("tags"), list) else ["local_action"]
    mid, created = insert_memory(
        source_type="local_action_note",
        source_key=None,
        title=title,
        url=None,
        content=content,
        importance=max(0.0, min(1.0, float(payload.get("importance", 0.55)))),
        tags=[str(x)[:100] for x in tags],
        summary=clean_summary(content),
        sensitivity="private",
        allow_external_llm=False,
        db_path=db_path,
    )
    index_memory(mid, title, content, clean_summary(content), db_path=db_path)
    return {"memory_id": mid, "created": created}, {"memory_id": mid, "previous_status": "active"}


def propose_action(
    action_type: str,
    description: str,
    payload: dict[str, Any] | None = None,
    *,
    db_path: Path | None = None,
) -> dict[str, Any]:
    if action_type not in ACTION_SPECS:
        raise ValueError(f"Unsupported action_type: {action_type}")
    spec = ACTION_SPECS[action_type]
    payload = payload or {}
    policy = action_policy(risk=spec.risk, reversible=spec.reversible, external_side_effect=spec.external_side_effect)

    approval_id: int | None = None
    result: dict[str, Any] = {}
    undo_payload: dict[str, Any] = {}
    status = "proposed"

    # Only explicitly implemented local reversible actions may auto-execute.
    if policy["auto_execute"] and spec.executor == "local_note":
        result, undo_payload = _execute_local_note(payload, db_path=db_path)
        status = "done"
    else:
        # External side effects and high-impact actions remain proposal-only in this alpha.
        approval_id = _create_approval(action_type, description, spec.risk, payload, db_path=db_path)
        status = "awaiting_approval" if policy["approval_required"] else "proposed"

    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO action_runs(created_at,action_type,description,risk,mode,status,reversible,external_side_effect,payload,result,approval_id,undo_payload) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                now_iso(), action_type, description[:2000], spec.risk, policy["mode"], status,
                int(spec.reversible), int(spec.external_side_effect), json.dumps(payload, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False), approval_id, json.dumps(undo_payload, ensure_ascii=False),
            ),
        )
        action_id = int(cur.lastrowid)
    return {
        "id": action_id,
        "action_type": action_type,
        "status": status,
        "policy": policy,
        "approval_id": approval_id,
        "result": result,
        "reversible": spec.reversible,
        "external_side_effect": spec.external_side_effect,
        "note": "External writes are proposal-only in v0.7.2-alpha." if spec.external_side_effect else "",
    }


def list_actions(limit: int = 100, *, db_path: Path | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM action_runs ORDER BY id DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        d = dict(row)
        for key in ("payload", "result", "undo_payload"):
            try:
                d[key] = json.loads(d.get(key) or "{}")
            except Exception:
                d[key] = {}
        out.append(d)
    return out


def undo_action(action_id: int, *, db_path: Path | None = None) -> dict[str, Any]:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM action_runs WHERE id=?", (action_id,)).fetchone()
        if not row:
            raise KeyError(action_id)
        item = dict(row)
        if item["status"] != "done" or not bool(item["reversible"]):
            raise ValueError("Action is not an executed reversible action")
        try:
            undo = json.loads(item.get("undo_payload") or "{}")
        except Exception:
            undo = {}
        if item["action_type"] == "create_local_note":
            memory_id = int(undo.get("memory_id") or 0)
            if not memory_id:
                raise ValueError("Missing undo memory id")
            conn.execute("UPDATE memories SET status='archived' WHERE id=?", (memory_id,))
        else:
            raise ValueError("No undo executor for this action")
        conn.execute("UPDATE action_runs SET status='undone',undone_at=? WHERE id=?", (now_iso(), action_id))
    return {"id": action_id, "status": "undone"}
