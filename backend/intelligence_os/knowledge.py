from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import connect, now_iso


def _iso_or_none(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return value[:80]


def source_fingerprint(*, url: str | None, title: str, content: str) -> str:
    raw = f"{url or ''}\n{title}\n{content}".encode("utf-8", "ignore")
    return hashlib.sha256(raw).hexdigest()


def register_provenance(
    memory_id: int,
    *,
    title: str,
    content: str,
    url: str | None,
    source_kind: str = "captured",
    publisher: str | None = None,
    published_at: str | None = None,
    authority: float | None = None,
    trust: str = "untrusted_external",
    db_path: Path | None = None,
) -> int:
    authority = 0.5 if authority is None else max(0.0, min(1.0, float(authority)))
    fp = source_fingerprint(url=url, title=title, content=content)
    with connect(db_path) as conn:
        row = conn.execute("SELECT id FROM provenance WHERE memory_id=?", (memory_id,)).fetchone()
        values = (
            source_kind, publisher, _iso_or_none(published_at), now_iso(), authority,
            trust, url, fp, memory_id,
        )
        if row:
            conn.execute(
                "UPDATE provenance SET source_kind=?,publisher=?,published_at=?,retrieved_at=?,authority=?,trust=?,canonical_url=?,fingerprint=? WHERE memory_id=?",
                values,
            )
            return int(row["id"])
        cur = conn.execute(
            "INSERT INTO provenance(created_at,memory_id,source_kind,publisher,published_at,retrieved_at,authority,trust,canonical_url,fingerprint) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (now_iso(), memory_id, source_kind, publisher, _iso_or_none(published_at), now_iso(), authority, trust, url, fp),
        )
        return int(cur.lastrowid)


def create_claim(
    text: str,
    *,
    topic_key: str | None = None,
    origin_memory_id: int | None = None,
    origin_task_id: int | None = None,
    db_path: Path | None = None,
) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO claims(created_at,claim_text,topic_key,origin_memory_id,origin_task_id,status,confidence,verification_method) VALUES(?,?,?,?,?,?,?,?)",
            (now_iso(), text.strip(), topic_key, origin_memory_id, origin_task_id, "unverified", 0.0, "none"),
        )
        return int(cur.lastrowid)



def get_or_create_claim(
    text: str,
    *,
    topic_key: str | None = None,
    origin_memory_id: int | None = None,
    origin_task_id: int | None = None,
    db_path: Path | None = None,
) -> tuple[int, bool]:
    normalized = text.strip()
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM claims WHERE claim_text=? AND COALESCE(topic_key,'')=COALESCE(?,'') AND status<>'superseded' ORDER BY id DESC LIMIT 1",
            (normalized, topic_key),
        ).fetchone()
        if row:
            return int(row["id"]), False
    return create_claim(normalized, topic_key=topic_key, origin_memory_id=origin_memory_id, origin_task_id=origin_task_id, db_path=db_path), True


def prepare_reverification(claim_id: int, *, db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        c = conn.execute("SELECT status,confidence,verification_method,verified_at FROM claims WHERE id=?", (claim_id,)).fetchone()
        if not c:
            raise KeyError(claim_id)
        if c["verified_at"]:
            conn.execute(
                "INSERT INTO claim_history(created_at,claim_id,previous_status,previous_confidence,previous_method,previous_verified_at) VALUES(?,?,?,?,?,?)",
                (now_iso(), claim_id, c["status"], c["confidence"], c["verification_method"], c["verified_at"]),
            )
        # Current evidence is recomputed; claim_history keeps the prior verdict snapshot.
        conn.execute("DELETE FROM evidence WHERE claim_id=?", (claim_id,))
        conn.execute("UPDATE claims SET status='unverified',confidence=0.0,verification_method='none',verified_at=NULL WHERE id=?", (claim_id,))

def update_claim_verdict(
    claim_id: int,
    *,
    status: str,
    confidence: float,
    method: str,
    db_path: Path | None = None,
) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE claims SET status=?,confidence=?,verification_method=?,verified_at=? WHERE id=?",
            (status, max(0.0, min(1.0, confidence)), method, now_iso(), claim_id),
        )


def add_evidence(
    claim_id: int,
    memory_id: int,
    *,
    stance: str,
    score: float,
    source_quality: float,
    freshness: float,
    directness: float,
    excerpt: str,
    rationale: str,
    method: str,
    injection_risk: bool = False,
    db_path: Path | None = None,
) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO evidence(created_at,claim_id,memory_id,stance,score,source_quality,freshness,directness,excerpt,rationale,method,injection_risk) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                now_iso(), claim_id, memory_id, stance, score, source_quality, freshness,
                directness, excerpt[:3000], rationale[:1200], method, int(bool(injection_risk)),
            ),
        )
        eid = int(cur.lastrowid)
        if stance == "contradicts" and score >= 0.5:
            conn.execute(
                "INSERT INTO contradictions(created_at,claim_id,evidence_id,severity,status) VALUES(?,?,?,?,?)",
                (now_iso(), claim_id, eid, min(1.0, score), "open"),
            )
        return eid


def mark_contested_previous_claims(
    new_claim_id: int,
    *,
    conflicts_with: list[int],
    db_path: Path | None = None,
) -> None:
    if not conflicts_with:
        return
    with connect(db_path) as conn:
        for old_id in conflicts_with:
            if old_id == new_claim_id:
                continue
            conn.execute(
                "UPDATE claims SET status='contested' WHERE id=? AND status IN ('verified','supported')",
                (old_id,),
            )
            conn.execute(
                "INSERT INTO claim_relations(created_at,from_claim_id,to_claim_id,relation,status) VALUES(?,?,?,?,?)",
                (now_iso(), old_id, new_claim_id, "conflicts_with", "open"),
            )


def correct_claim(claim_id: int, correction: str, *, db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT id FROM claims WHERE id=?", (claim_id,)).fetchone()
        if not row:
            raise KeyError(claim_id)
        conn.execute(
            "UPDATE claims SET user_correction=?,status='corrected',verified_at=? WHERE id=?",
            (correction.strip(), now_iso(), claim_id),
        )


def supersede_claim(old_claim_id: int, new_claim_id: int, *, db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        old = conn.execute("SELECT id FROM claims WHERE id=?", (old_claim_id,)).fetchone()
        new = conn.execute("SELECT id FROM claims WHERE id=?", (new_claim_id,)).fetchone()
        if not old or not new:
            raise KeyError("claim not found")
        conn.execute("UPDATE claims SET status='superseded',superseded_by=? WHERE id=?", (new_claim_id, old_claim_id))
        conn.execute(
            "INSERT INTO claim_relations(created_at,from_claim_id,to_claim_id,relation,status) VALUES(?,?,?,?,?)",
            (now_iso(), old_claim_id, new_claim_id, "superseded_by", "confirmed"),
        )


def claim_detail(claim_id: int, *, db_path: Path | None = None) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        c = conn.execute("SELECT * FROM claims WHERE id=?", (claim_id,)).fetchone()
        if not c:
            return None
        e = conn.execute(
            "SELECT e.*,m.title AS source_title,m.url AS source_url,p.publisher,p.published_at,p.authority,p.trust "
            "FROM evidence e JOIN memories m ON m.id=e.memory_id LEFT JOIN provenance p ON p.memory_id=m.id "
            "WHERE e.claim_id=? ORDER BY e.score DESC,e.id DESC",
            (claim_id,),
        ).fetchall()
        rel = conn.execute(
            "SELECT * FROM claim_relations WHERE from_claim_id=? OR to_claim_id=? ORDER BY id DESC",
            (claim_id, claim_id),
        ).fetchall()
        hist = conn.execute("SELECT * FROM claim_history WHERE claim_id=? ORDER BY id DESC", (claim_id,)).fetchall()
    out = dict(c)
    out["evidence"] = [dict(r) for r in e]
    out["relations"] = [dict(r) for r in rel]
    out["history"] = [dict(r) for r in hist]
    return out


def knowledge_status(*, db_path: Path | None = None) -> dict[str, int]:
    with connect(db_path) as conn:
        rows = conn.execute("SELECT status,COUNT(*) n FROM claims GROUP BY status").fetchall()
        contradictions = conn.execute("SELECT COUNT(*) n FROM contradictions WHERE status='open'").fetchone()["n"]
        sources = conn.execute("SELECT COUNT(*) n FROM provenance").fetchone()["n"]
    counts = {str(r["status"]): int(r["n"]) for r in rows}
    return {"sources": int(sources), "open_contradictions": int(contradictions), **counts}
