from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .knowledge import register_provenance
from .retrieval import index_memory
from .storage import clean_summary, connect, insert_memory, now_iso


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def create_expectation(
    prediction_text: str,
    expected_result: str,
    confidence: float,
    *,
    due_at: str | None = None,
    origin_task_id: int | None = None,
    db_path: Path | None = None,
) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO expectations(created_at,prediction_text,expected_result,confidence,due_at,origin_task_id,status) VALUES(?,?,?,?,?,?,?)",
            (now_iso(), prediction_text.strip(), expected_result.strip(), _clamp01(confidence), due_at, origin_task_id, "open"),
        )
        return int(cur.lastrowid)


def create_decision(
    title: str,
    choice: str,
    *,
    rationale: str = "",
    expectation_id: int | None = None,
    db_path: Path | None = None,
) -> int:
    with connect(db_path) as conn:
        if expectation_id is not None and not conn.execute("SELECT 1 FROM expectations WHERE id=?", (expectation_id,)).fetchone():
            raise KeyError(expectation_id)
        cur = conn.execute(
            "INSERT INTO decisions(created_at,title,choice,rationale,expectation_id,status) VALUES(?,?,?,?,?,?)",
            (now_iso(), title.strip(), choice.strip(), rationale.strip(), expectation_id, "active"),
        )
        return int(cur.lastrowid)


def record_outcome(
    expectation_id: int,
    observed_text: str,
    match_score: float,
    *,
    decision_id: int | None = None,
    observed_at: str | None = None,
    source: str = "human",
    db_path: Path | None = None,
) -> int:
    with connect(db_path) as conn:
        if not conn.execute("SELECT 1 FROM expectations WHERE id=?", (expectation_id,)).fetchone():
            raise KeyError(expectation_id)
        if decision_id is not None and not conn.execute("SELECT 1 FROM decisions WHERE id=?", (decision_id,)).fetchone():
            raise KeyError(decision_id)
        cur = conn.execute(
            "INSERT INTO outcomes(created_at,expectation_id,decision_id,observed_text,match_score,observed_at,source) VALUES(?,?,?,?,?,?,?)",
            (now_iso(), expectation_id, decision_id, observed_text.strip(), _clamp01(match_score), observed_at or now_iso(), source),
        )
        conn.execute("UPDATE expectations SET status='observed' WHERE id=?", (expectation_id,))
        return int(cur.lastrowid)


def propose_reflection(expectation_id: int, *, db_path: Path | None = None) -> dict[str, Any]:
    with connect(db_path) as conn:
        exp = conn.execute("SELECT * FROM expectations WHERE id=?", (expectation_id,)).fetchone()
        if not exp:
            raise KeyError(expectation_id)
        out = conn.execute("SELECT * FROM outcomes WHERE expectation_id=? ORDER BY id DESC LIMIT 1", (expectation_id,)).fetchone()
        if not out:
            raise ValueError("No outcome recorded for expectation")
        existing = conn.execute("SELECT * FROM lessons WHERE expectation_id=? AND outcome_id=? ORDER BY id DESC LIMIT 1", (expectation_id, out["id"])).fetchone()
        if existing:
            return dict(existing)

        # match_score is a human-assessed degree of outcome match, not a probabilistic observation.
        # Therefore abs(confidence-match_score) is NOT a calibration error. We track two honest metrics:
        # outcome_mismatch = how far the observed result was from the expected result, and
        # surprise_score = mismatch weighted by how confident the original expectation was.
        mismatch = round(1.0 - float(out["match_score"]), 3)
        surprise = round(float(exp["confidence"]) * mismatch, 3)
        if float(out["match_score"]) >= 0.75:
            lesson = "The expectation was broadly consistent with the observed outcome. Preserve the useful assumptions but avoid overgeneralizing from one result."
            rule = "Reuse this reasoning only when the key assumptions and context match; continue outcome tracking."
        elif float(out["match_score"]) <= 0.35:
            lesson = "The observed outcome differed materially from the expectation. Revisit the assumptions, missing variables, and evidence that drove the original prediction."
            rule = "Before a similar future decision, explicitly identify the assumptions that could make this prediction fail and seek disconfirming evidence."
        else:
            lesson = "The outcome only partially matched the expectation. Keep the parts that worked, and isolate which assumptions or conditions explain the mismatch."
            rule = "For similar cases, separate stable factors from context-dependent factors before estimating confidence."
        cur = conn.execute(
            "INSERT INTO lessons(created_at,expectation_id,outcome_id,lesson_text,proposed_rule,calibration_error,outcome_mismatch,surprise_score,status) VALUES(?,?,?,?,?,?,?,?,?)",
            (now_iso(), expectation_id, out["id"], lesson, rule, mismatch, mismatch, surprise, "proposed"),
        )
        lesson_id = int(cur.lastrowid)
        return dict(conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone())


def decide_lesson(
    lesson_id: int,
    *,
    accept: bool,
    human_note: str = "",
    db_path: Path | None = None,
) -> dict[str, Any]:
    with connect(db_path) as conn:
        lesson = conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
        if not lesson:
            raise KeyError(lesson_id)
        exp = conn.execute("SELECT * FROM expectations WHERE id=?", (lesson["expectation_id"],)).fetchone()
        out = conn.execute("SELECT * FROM outcomes WHERE id=?", (lesson["outcome_id"],)).fetchone()

    memory_id = None
    status = "accepted" if accept else "rejected"
    if accept:
        content = (
            f"Expectation: {exp['prediction_text']}\nExpected result: {exp['expected_result']}\n"
            f"Observed outcome: {out['observed_text']}\n"
            f"Lesson: {lesson['lesson_text']}\nProposed future rule: {lesson['proposed_rule']}\n"
            f"Human note: {human_note.strip()}"
        )
        memory_id, _ = insert_memory(
            source_type="accepted_learning",
            source_key=f"lesson:{lesson_id}",
            title=f"Accepted lesson #{lesson_id}",
            url=None,
            content=content,
            importance=0.82,
            tags=["learning", "outcome"],
            summary=clean_summary(content),
            sensitivity="private",
            allow_external_llm=False,
            db_path=db_path,
        )
        index_memory(memory_id, f"Accepted lesson #{lesson_id}", content, clean_summary(content), db_path=db_path)
        register_provenance(
            memory_id,
            title=f"Accepted lesson #{lesson_id}",
            content=content,
            url=None,
            source_kind="human_accepted_learning",
            publisher="Human + Intelligence OS",
            # Human acceptance makes this authoritative about the user's own learning record, not
            # a high-authority external factual source. Keep factual authority deliberately modest.
            authority=0.55,
            trust="human_confirmed_personal_learning",
            db_path=db_path,
        )

    with connect(db_path) as conn:
        conn.execute(
            "UPDATE lessons SET status=?,human_note=?,decided_at=?,memory_id=? WHERE id=?",
            (status, human_note.strip(), now_iso(), memory_id, lesson_id),
        )
        conn.execute("UPDATE expectations SET status=? WHERE id=?", ("learned" if accept else "reviewed", lesson["expectation_id"]))
        return dict(conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone())


def learning_detail(expectation_id: int, *, db_path: Path | None = None) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        exp = conn.execute("SELECT * FROM expectations WHERE id=?", (expectation_id,)).fetchone()
        if not exp:
            return None
        outcomes = conn.execute("SELECT * FROM outcomes WHERE expectation_id=? ORDER BY id DESC", (expectation_id,)).fetchall()
        lessons = conn.execute("SELECT * FROM lessons WHERE expectation_id=? ORDER BY id DESC", (expectation_id,)).fetchall()
        decisions = conn.execute("SELECT * FROM decisions WHERE expectation_id=? ORDER BY id DESC", (expectation_id,)).fetchall()
    result = dict(exp)
    result["decisions"] = [dict(r) for r in decisions]
    result["outcomes"] = [dict(r) for r in outcomes]
    result["lessons"] = [dict(r) for r in lessons]
    return result


def learning_status(*, db_path: Path | None = None) -> dict[str, Any]:
    with connect(db_path) as conn:
        expectations = conn.execute("SELECT status,COUNT(*) n FROM expectations GROUP BY status").fetchall()
        lessons = conn.execute("SELECT status,COUNT(*) n FROM lessons GROUP BY status").fetchall()
        row = conn.execute("SELECT AVG(outcome_mismatch) avg_mismatch, AVG(surprise_score) avg_surprise FROM lessons").fetchone()
    return {
        "expectations": {r["status"]: int(r["n"]) for r in expectations},
        "lessons": {r["status"]: int(r["n"]) for r in lessons},
        "mean_outcome_mismatch": round(float(row["avg_mismatch"] or 0.0), 3),
        "mean_surprise_score": round(float(row["avg_surprise"] or 0.0), 3),
    }
