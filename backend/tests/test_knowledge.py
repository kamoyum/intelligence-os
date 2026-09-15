from pathlib import Path

from intelligence_os.knowledge import (
    claim_detail,
    correct_claim,
    create_claim,
    knowledge_status,
    register_provenance,
    supersede_claim,
)
from intelligence_os.storage import connect, init_db, insert_memory, clean_summary


def _memory(db: Path, title: str, content: str) -> int:
    mid, _ = insert_memory(
        source_type="test", source_key=title, title=title, content=content, url="https://example.test/source",
        importance=0.7, tags=[], summary=clean_summary(content), db_path=db,
    )
    return mid


def test_knowledge_schema_and_provenance(tmp_path: Path):
    db = tmp_path / "k.db"
    init_db(db)
    mid = _memory(db, "Official source", "Alpha is enabled by default.")
    pid = register_provenance(
        mid, title="Official source", content="Alpha is enabled by default.", url="https://example.test/source",
        source_kind="official", publisher="Example Authority", published_at="2026-01-01T00:00:00+00:00",
        authority=0.9, trust="untrusted_external", db_path=db,
    )
    assert pid > 0
    with connect(db) as conn:
        names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
    assert {"provenance", "claims", "evidence", "contradictions", "claim_relations"}.issubset(names)
    assert knowledge_status(db_path=db)["sources"] == 1


def test_correction_and_supersession_are_explicit_human_lifecycle(tmp_path: Path):
    db = tmp_path / "lifecycle.db"
    init_db(db)
    old = create_claim("Alpha requires 3 sessions per week.", topic_key="alpha.frequency", db_path=db)
    new = create_claim("Alpha requires 2 sessions per week.", topic_key="alpha.frequency", db_path=db)
    correct_claim(old, "This was an older rule.", db_path=db)
    assert claim_detail(old, db_path=db)["status"] == "corrected"
    supersede_claim(old, new, db_path=db)
    d = claim_detail(old, db_path=db)
    assert d["status"] == "superseded"
    assert d["superseded_by"] == new


def test_reverification_reuses_claim_identity_and_keeps_history(tmp_path: Path):
    from intelligence_os.knowledge import get_or_create_claim, prepare_reverification, update_claim_verdict
    db = tmp_path / "history.db"
    init_db(db)
    cid, created = get_or_create_claim("Alpha is enabled.", topic_key="alpha.enabled", db_path=db)
    assert created is True
    update_claim_verdict(cid, status="verified", confidence=0.8, method="test", db_path=db)
    cid2, created2 = get_or_create_claim("Alpha is enabled.", topic_key="alpha.enabled", db_path=db)
    assert cid2 == cid and created2 is False
    prepare_reverification(cid, db_path=db)
    d = claim_detail(cid, db_path=db)
    assert d["status"] == "unverified"
    assert len(d["history"]) == 1
    assert d["history"][0]["previous_status"] == "verified"
