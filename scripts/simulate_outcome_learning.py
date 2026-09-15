#!/usr/bin/env python3
"""Deterministic v0.6-alpha Outcome Learning simulation."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from intelligence_os.learning import (
    create_decision,
    create_expectation,
    decide_lesson,
    learning_detail,
    learning_status,
    propose_reflection,
    record_outcome,
)
from intelligence_os.storage import connect, init_db


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "learning.db"
        init_db(db)

        expectation_id = create_expectation(
            "Automation A will materially reduce processing time.",
            "At least 30% shorter processing time.",
            0.80,
            db_path=db,
        )
        decision_id = create_decision(
            "Pilot Automation A",
            "Use Automation A for the pilot workflow.",
            rationale="Expected time saving with low operational risk.",
            expectation_id=expectation_id,
            db_path=db,
        )
        outcome_id = record_outcome(
            expectation_id,
            "Observed processing time fell by only about 5% because manual review remained the bottleneck.",
            0.20,
            decision_id=decision_id,
            db_path=db,
        )
        lesson = propose_reflection(expectation_id, db_path=db)

        with connect(db) as conn:
            before = conn.execute("SELECT COUNT(*) n FROM memories WHERE source_type='accepted_learning'").fetchone()["n"]

        accepted = decide_lesson(
            lesson["id"],
            accept=True,
            human_note="The bottleneck was not the automated step; next pilot should measure the full workflow first.",
            db_path=db,
        )
        detail = learning_detail(expectation_id, db_path=db)
        status = learning_status(db_path=db)

        with connect(db) as conn:
            after = conn.execute("SELECT COUNT(*) n FROM memories WHERE source_type='accepted_learning'").fetchone()["n"]
            memory = conn.execute("SELECT id,title,content FROM memories WHERE id=?", (accepted["memory_id"],)).fetchone()

        report = {
            "simulation": "outcome_learning_fixture",
            "expectation_id": expectation_id,
            "decision_id": decision_id,
            "outcome_id": outcome_id,
            "lesson": {
                "id": lesson["id"],
                "status_before_human": lesson["status"],
                "outcome_mismatch": lesson["outcome_mismatch"], "surprise_score": lesson["surprise_score"],
                "proposed_rule": lesson["proposed_rule"],
            },
            "human_decision": {
                "status": accepted["status"],
                "memory_id": accepted["memory_id"],
            },
            "learning_status": status,
            "accepted_memory_title": memory["title"] if memory else None,
            "pass_conditions": {
                "prediction_recorded": detail is not None and detail["confidence"] == 0.8,
                "decision_linked": bool(detail and detail["decisions"] and detail["decisions"][0]["id"] == decision_id),
                "outcome_linked": bool(detail and detail["outcomes"] and detail["outcomes"][0]["id"] == outcome_id),
                "outcome_mismatch_calculated": lesson["outcome_mismatch"] == 0.8,
                "no_silent_learning": before == 0,
                "human_acceptance_required": accepted["status"] == "accepted",
                "accepted_lesson_promoted_to_memory": after == 1 and accepted["memory_id"] is not None,
                "expectation_lifecycle_closed": detail["status"] == "learned",
            },
        }
        report["all_pass"] = all(report["pass_conditions"].values())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
