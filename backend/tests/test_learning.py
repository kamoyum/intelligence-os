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


def test_outcome_learning_requires_human_acceptance(tmp_path):
    db = tmp_path / "learning.db"
    init_db(db)
    exp = create_expectation(
        "Automation A will reduce processing time materially.",
        "At least 30% shorter processing time.",
        0.8,
        db_path=db,
    )
    decision = create_decision("Use Automation A", "Adopt A for the pilot", rationale="Expected time saving", expectation_id=exp, db_path=db)
    outcome = record_outcome(exp, "Observed time reduction was only about 5%.", 0.2, decision_id=decision, db_path=db)
    lesson = propose_reflection(exp, db_path=db)
    assert lesson["status"] == "proposed"
    assert lesson["outcome_mismatch"] == 0.8
    assert lesson["surprise_score"] == 0.64

    # Proposed learning is not yet promoted into Memory.
    with connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) n FROM memories WHERE source_type='accepted_learning'").fetchone()["n"] == 0

    accepted = decide_lesson(lesson["id"], accept=True, human_note="Pilot context was narrower than expected.", db_path=db)
    assert accepted["status"] == "accepted"
    assert accepted["memory_id"] is not None
    detail = learning_detail(exp, db_path=db)
    assert detail["status"] == "learned"
    assert detail["outcomes"][0]["id"] == outcome
    status = learning_status(db_path=db)
    assert status["lessons"]["accepted"] == 1


def test_rejected_lesson_does_not_become_memory(tmp_path):
    db = tmp_path / "learning.db"
    init_db(db)
    exp = create_expectation("X", "Y", 0.5, db_path=db)
    record_outcome(exp, "Y partly happened", 0.5, db_path=db)
    lesson = propose_reflection(exp, db_path=db)
    rejected = decide_lesson(lesson["id"], accept=False, human_note="Not enough observations.", db_path=db)
    assert rejected["status"] == "rejected"
    assert rejected["memory_id"] is None
